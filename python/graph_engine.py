#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graph_engine.py — движок визуализации графов для конспекта КиТГ.

Возможности:
  * чтение/запись формата .graph (JSON, совместим с programforyou / graph.online);
  * конвертация в networkx (Graph / DiGraph);
  * статический рендер графа в PDF (render_graph);
  * пошаговый рендер с панелью пояснений (render_step);
  * набор алгоритмов, каждый из которых возвращает список шагов
    (с раскраской вершин/рёбер) и попутно генерирует .graph и .pdf для
    каждого шага: DFS, BFS, Дейкстра, Форд—Беллман, Прим, Краскал,
    топологическая сортировка, Форд—Фалкерсон.

Стиль: Python 3.10+, type hints, без сторонних зависимостей кроме
cairosvg, networkx и Node.js (для движка programforyou).
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import networkx as nx

import pfy_render  # офлайн-рендер .graph -> PDF движком programforyou


# =============================================================================
# Цветовая схема (см. KiTG_PROJECT_PLAN.md, раздел 3)
# =============================================================================

class Palette:
    """Палитра цветов для раскраски шагов алгоритмов."""

    # --- вершины ---
    V_IDLE_BG = "#ffffff"      # непосещённая
    V_IDLE_BORDER = "#000000"
    V_ACTIVE_BG = "#ff5722"    # текущая (активная)
    V_ACTIVE_BORDER = "#d32f2f"
    V_DONE_BG = "#4caf50"      # посещённая / обработанная
    V_DONE_BORDER = "#388e3c"
    V_QUEUE_BG = "#2196f3"     # в очереди / стеке
    V_QUEUE_BORDER = "#1565c0"
    V_FINAL_BG = "#ffc107"     # финальная (в ответе)
    V_FINAL_BORDER = "#ff8f00"

    V_REMOVED_BG = "#f2f2f2"   # удалённая (код Прюфера)
    V_REMOVED_BORDER = "#c4c4c4"
    V_REMOVED_TEXT = "#b0b0b0"

    # --- рёбра ---
    E_IDLE = "#cccccc"         # необработанное
    E_REMOVED = "#e6e6e6"      # ребро удалённой вершины
    LW_THIN = 1.0
    E_ACTIVE = "#ff5722"       # текущее (рассматриваем)
    E_TREE = "#4caf50"         # в ответе (дерево / путь / поток)
    E_RELAX = "#2196f3"        # релаксация / обновление
    E_BLACK = "#000000"        # обычное (статический рендер)

    LW_NORMAL = 2.0
    LW_THICK = 3.5


# =============================================================================
# Чтение / запись формата .graph
# =============================================================================

def load_graph(path: str | Path) -> dict[str, Any]:
    """Загружает .graph-файл (JSON) в словарь."""
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("vertices", [])
    data.setdefault("edges", [])
    data.setdefault("texts", [])
    return data


def save_graph(graph: dict[str, Any], path: str | Path) -> None:
    """Сохраняет словарь графа в .graph-файл (JSON)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(graph, fh, ensure_ascii=False, indent=2)


def _is_directed(graph: dict[str, Any]) -> bool:
    """Считает граф ориентированным, если хотя бы одно ребро направленное."""
    return any(bool(e.get("isDirected")) for e in graph.get("edges", []))


def graph_to_networkx(graph: dict[str, Any]) -> nx.Graph | nx.DiGraph:
    """Строит объект networkx из словаря .graph.

    Веса парсятся в float, если возможно; имена вершин используются как id.
    """
    directed = _is_directed(graph)
    g: nx.Graph | nx.DiGraph = nx.DiGraph() if directed else nx.Graph()

    for idx, v in enumerate(graph["vertices"]):
        g.add_node(v["name"], index=idx, **{k: v[k] for k in ("x", "y") if k in v})

    for e in graph["edges"]:
        u = graph["vertices"][e["vertex1"]]["name"]
        w = graph["vertices"][e["vertex2"]]["name"]
        weight = _parse_weight(e.get("weight", ""))
        g.add_edge(u, w, weight=weight, directed=bool(e.get("isDirected")))
    return g


def _norm_color(c: Any, fallback: str = "#000000") -> str:
    """Приводит цвет к виду, понятному matplotlib.

    Файлы .graph могут содержать CSS-цвета вида ``hsl(h,s%,l%)`` —
    matplotlib их не понимает, поэтому конвертируем в hex.
    """
    if not isinstance(c, str):
        return fallback
    s = c.strip()
    if s.startswith("#") or s.lower() in ("white", "black", "red", "blue", "green"):
        return s
    if s.lower().startswith("hsl"):
        nums = s[s.find("(") + 1: s.find(")")].split(",")
        try:
            h = float(nums[0]) / 360.0
            sat = float(nums[1].replace("%", "")) / 100.0
            light = float(nums[2].replace("%", "")) / 100.0
        except (ValueError, IndexError):
            return fallback
        import colorsys
        r, g, b = colorsys.hls_to_rgb(h, light, sat)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    if s.lower().startswith("rgb"):
        nums = s[s.find("(") + 1: s.find(")")].split(",")
        try:
            r, g, b = (int(float(n.replace("%", ""))) for n in nums[:3])
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return fallback
    return s if s else fallback


def _parse_weight(raw: Any) -> Optional[float]:
    """Пытается преобразовать вес ребра в число. None — если не получилось."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


# =============================================================================
# Вспомогательные функции раскраски
# =============================================================================

def _name_to_index(graph: dict[str, Any]) -> dict[str, int]:
    return {v["name"]: i for i, v in enumerate(graph["vertices"])}


def color_vertex(graph: dict[str, Any], name: str, bg: str, border: str) -> None:
    """Перекрашивает вершину по имени."""
    for v in graph["vertices"]:
        if v["name"] == name:
            v["background"] = bg
            v["border"] = border
            return


def color_edge(
    graph: dict[str, Any],
    u: str,
    w: str,
    color: str,
    line_width: float | None = None,
    *,
    directed_only: bool = False,
) -> None:
    """Перекрашивает ребро (u, w). Для неориентированного — в любом порядке."""
    idx = _name_to_index(graph)
    iu, iw = idx.get(u), idx.get(w)
    if iu is None or iw is None:
        return
    for e in graph["edges"]:
        a, b = e["vertex1"], e["vertex2"]
        match = (a == iu and b == iw)
        if not directed_only and not e.get("isDirected"):
            match = match or (a == iw and b == iu)
        if match:
            e["color"] = color
            e["background"] = color
            if line_width is not None:
                e["lineWidth"] = line_width
            return


def reset_colors(graph: dict[str, Any]) -> dict[str, Any]:
    """Возвращает копию графа со сброшенными в нейтраль цветами."""
    g = copy.deepcopy(graph)
    for v in g["vertices"]:
        v["background"] = Palette.V_IDLE_BG
        v["border"] = Palette.V_IDLE_BORDER
        v["color"] = v.get("color", "#000000")
    for e in g["edges"]:
        e["color"] = Palette.E_IDLE
        e["background"] = Palette.E_IDLE
        e["lineWidth"] = Palette.LW_NORMAL
    return g


# =============================================================================
# Рендер (через офлайн-движок programforyou: .graph -> SVG -> PDF)
# =============================================================================

@dataclass
class StepInfo:
    """Метаданные одного шага алгоритма (заголовок/описание для подписи в LaTeX)."""
    number: int
    title: str = ""
    description: str = ""


def render_graph(graph: dict[str, Any], output_path: str | Path,
                 *, title: str | None = None,
                 annotations: Optional[list[str]] = None) -> None:
    """Рендерит граф в PDF движком programforyou.

    Цвета берутся из самих полей вершин/рёбер (.graph). Заголовок и пояснения
    в КАРТИНКУ не вшиваются (они идут подписью в LaTeX) — это убирает кривые
    «боковые панели» прежнего matplotlib-рендера.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # programforyou-движок читает .graph-файл, поэтому сохраняем словарь во временный файл.
    import tempfile, json as _json
    with tempfile.NamedTemporaryFile("w", suffix=".graph", delete=False,
                                     encoding="utf-8") as tmp:
        _json.dump(graph, tmp, ensure_ascii=False)
        tmp_path = tmp.name
    try:
        pfy_render.render_to_pdf(tmp_path, output_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def render_step(graph: dict[str, Any], step_info: "StepInfo",
                output_path: str | Path,
                annotations: Optional[list[str]] = None) -> None:
    """Рендерит один шаг алгоритма (просто окрашенный граф)."""
    render_graph(graph, output_path)


# =============================================================================
# Каркас алгоритма: накапливает шаги, пишет .graph и .pdf
# =============================================================================

@dataclass
class StepRecorder:
    """Накопитель шагов: сохраняет окрашенные состояния графа в .graph и .pdf."""
    base_dir: Path
    name: str            # префикс файлов, напр. "1-dfs"
    steps: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        graph: dict[str, Any],
        title: str,
        description: str = "",
        annotations: Optional[list[str]] = None,
    ) -> None:
        n = len(self.steps)
        snapshot = copy.deepcopy(graph)
        graph_path = self.base_dir / f"{self.name}-{n}.graph"
        pdf_path = self.base_dir / f"{self.name}-{n}.pdf"
        save_graph(snapshot, graph_path)
        render_step(snapshot, StepInfo(n, title, description), pdf_path,
                    annotations=annotations)
        self.steps.append(
            {"number": n, "title": title, "description": description,
             "graph": str(graph_path), "pdf": str(pdf_path)}
        )

    def finish(self) -> list[dict[str, Any]]:
        return self.steps


def _adjacency(graph: dict[str, Any]) -> tuple[list[str], dict[str, list[tuple[str, Optional[float]]]]]:
    """Строит список имён вершин и список смежности (с учётом направленности)."""
    names = [v["name"] for v in graph["vertices"]]
    adj: dict[str, list[tuple[str, Optional[float]]]] = {n: [] for n in names}
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}
    for e in graph["edges"]:
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        wt = _parse_weight(e.get("weight", ""))
        adj[u].append((w, wt))
        if not e.get("isDirected"):
            adj[w].append((u, wt))
    return names, adj


# =============================================================================
# Алгоритмы
# =============================================================================

def run_dfs(graph: dict[str, Any], start: str, base_dir: Path, name: str) -> list[dict[str, Any]]:
    """Поиск в глубину. Раскраска: стек — синий, текущая — оранжевая, готовая — зелёная."""
    names, adj = _adjacency(graph)
    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=[f"Старт из вершины {start}"])

    visited: set[str] = set()
    order: list[str] = []
    stack = [start]
    color_vertex(g, start, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
    rec.add(g, "В стек добавлен старт", annotations=[f"Стек: [{start}]"])

    while stack:
        u = stack.pop()
        if u in visited:
            continue
        visited.add(u)
        order.append(u)
        color_vertex(g, u, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        rec.add(g, f"Обрабатываем {u}",
                annotations=[f"Извлекли {u} из стека", f"Порядок обхода: {', '.join(order)}"])
        for w, _ in sorted(adj[u]):
            if w not in visited:
                stack.append(w)
                color_edge(g, u, w, Palette.E_TREE, Palette.LW_THICK)
                color_vertex(g, w, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
        color_vertex(g, u, Palette.V_DONE_BG, Palette.V_DONE_BORDER)

    for n in order:
        color_vertex(g, n, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
    rec.add(g, "Готово", annotations=[f"Порядок DFS: {', '.join(order)}"])
    return rec.finish()


def run_bfs(graph: dict[str, Any], start: str, base_dir: Path, name: str) -> list[dict[str, Any]]:
    """Поиск в ширину."""
    from collections import deque

    names, adj = _adjacency(graph)
    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=[f"Старт из вершины {start}"])

    visited = {start}
    order: list[str] = []
    queue = deque([start])
    color_vertex(g, start, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
    rec.add(g, "В очередь добавлен старт", annotations=[f"Очередь: [{start}]"])

    while queue:
        u = queue.popleft()
        order.append(u)
        color_vertex(g, u, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        new_nodes = []
        for w, _ in sorted(adj[u]):
            if w not in visited:
                visited.add(w)
                queue.append(w)
                new_nodes.append(w)
                color_edge(g, u, w, Palette.E_TREE, Palette.LW_THICK)
                color_vertex(g, w, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
        ann = [f"Обрабатываем {u}", f"Уровень соседей: {', '.join(new_nodes) or '—'}"]
        rec.add(g, f"Обрабатываем {u}", annotations=ann)
        color_vertex(g, u, Palette.V_DONE_BG, Palette.V_DONE_BORDER)

    rec.add(g, "Готово", annotations=[f"Порядок BFS: {', '.join(order)}"])
    return rec.finish()


def run_dijkstra(graph: dict[str, Any], start: str, base_dir: Path, name: str) -> list[dict[str, Any]]:
    """Алгоритм Дейкстры (неотрицательные веса)."""
    import heapq

    names, adj = _adjacency(graph)
    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    INF = math.inf
    dist = {n: INF for n in names}
    dist[start] = 0.0
    rec.add(g, "Инициализация",
            annotations=[f"d[{start}]=0, остальные = ∞"])

    pq: list[tuple[float, str]] = [(0.0, start)]
    done: set[str] = set()
    color_vertex(g, start, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)

    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        color_vertex(g, u, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        relaxed = []
        for w, wt in sorted(adj[u]):
            if wt is None:
                wt = 1.0
            nd = d + wt
            if nd < dist[w]:
                dist[w] = nd
                heapq.heappush(pq, (nd, w))
                color_edge(g, u, w, Palette.E_RELAX, Palette.LW_THICK)
                if w not in done:
                    color_vertex(g, w, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
                relaxed.append(f"d[{w}]={_fmt(nd)}")
        ann = [f"Фиксируем {u}, d[{u}]={_fmt(d)}"]
        if relaxed:
            ann.append("Обновили: " + ", ".join(relaxed))
        rec.add(g, f"Фиксируем {u}", annotations=ann)
        color_vertex(g, u, Palette.V_DONE_BG, Palette.V_DONE_BORDER)

    final = ", ".join(f"{n}:{_fmt(dist[n])}" for n in names)
    rec.add(g, "Готово", annotations=["Кратчайшие расстояния:", final])
    return rec.finish()


def run_bellman_ford(graph: dict[str, Any], start: str, base_dir: Path, name: str) -> list[dict[str, Any]]:
    """Алгоритм Форда—Беллмана (допускает отрицательные веса)."""
    names, adj = _adjacency(graph)
    edges: list[tuple[str, str, float]] = []
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}
    for e in graph["edges"]:
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        wt = _parse_weight(e.get("weight", "")) or 0.0
        edges.append((u, w, wt))
        if not e.get("isDirected"):
            edges.append((w, u, wt))

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    for e in g["edges"]:
        e["color"] = Palette.E_BLACK
        e["background"] = Palette.E_BLACK
    dist = {n: math.inf for n in names}
    dist[start] = 0.0
    color_vertex(g, start, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
    rec.add(g, "Инициализация", annotations=[f"d[{start}]=0, остальные = ∞"])

    for it in range(len(names) - 1):
        relaxed_edges: list[tuple[str, str]] = []
        changed: list[str] = []
        for u, w, wt in edges:
            if dist[u] + wt < dist[w]:
                dist[w] = dist[u] + wt
                relaxed_edges.append((u, w))
                changed.append(f"d[{w}]={_fmt(dist[w])}")
        if not changed:
            rec.add(g, f"Итерация {it + 1}: без изменений",
                    annotations=["Расстояния стабилизировались"])
            break
        gg = reset_colors(graph)
        for e in gg["edges"]:
            e["color"] = Palette.E_BLACK
            e["background"] = Palette.E_BLACK
        for n in names:
            if dist[n] < math.inf:
                if n == start:
                    color_vertex(gg, n, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
                else:
                    color_vertex(gg, n, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        for u, w in relaxed_edges:
            color_edge(gg, u, w, Palette.E_RELAX, Palette.LW_THICK, directed_only=True)
        for u, w in relaxed_edges:
            color_vertex(gg, w, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        rec.add(gg, f"Итерация {it + 1}",
                annotations=["Рассмотрели все рёбра",
                             "Обновили: " + ", ".join(changed[:6]) + ("…" if len(changed) > 6 else "")])
        g = gg

    final = ", ".join(f"{n}:{_fmt(dist[n])}" for n in names)
    rec.add(g, "Готово", annotations=["Кратчайшие расстояния:", final])
    return rec.finish()


def run_prim(graph: dict[str, Any], start: str, base_dir: Path, name: str) -> list[dict[str, Any]]:
    """Алгоритм Прима (минимальное остовное дерево)."""
    import heapq

    names, adj = _adjacency(graph)
    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    in_tree = {start}
    color_vertex(g, start, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
    rec.add(g, "Инициализация", annotations=[f"Дерево = {{{start}}}"])

    pq: list[tuple[float, str, str]] = []
    for w, wt in adj[start]:
        heapq.heappush(pq, (wt if wt is not None else 1.0, start, w))

    total = 0.0
    while pq and len(in_tree) < len(names):
        wt, u, w = heapq.heappop(pq)
        if w in in_tree:
            continue
        in_tree.add(w)
        total += wt
        color_edge(g, u, w, Palette.E_TREE, Palette.LW_THICK)
        color_vertex(g, w, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        rec.add(g, f"Добавляем ребро {u}—{w}",
                annotations=[f"Вес = {_fmt(wt)}", f"Сумма = {_fmt(total)}"])
        for x, xwt in adj[w]:
            if x not in in_tree:
                heapq.heappush(pq, (xwt if xwt is not None else 1.0, w, x))

    rec.add(g, "Остов построен", annotations=[f"Суммарный вес = {_fmt(total)}"])
    return rec.finish()


def run_pruefer(graph: dict[str, Any], base_dir: Path, name: str, **_: Any) -> list[dict[str, Any]]:
    """Код Прюфера (прямая задача): пока в дереве больше двух вершин, удаляем
    лист с минимальной меткой и дописываем в код его соседа.

    Вершины из снапшота не удаляются физически — «удалённые» закрашиваются
    серым (V_REMOVED_*), их рёбра — светло-серым тонким (E_REMOVED), так что
    на каждом кадре видна и история, и оставшееся дерево.
    """
    names, adj = _adjacency(graph)
    neigh: dict[str, set[str]] = {n: {w for w, _ in adj[n]} for n in names}
    removed: set[str] = set()
    code: list[str] = []

    def _grey_out(g: dict[str, Any]) -> None:
        """Перекрашивает все ранее удалённые вершины и их рёбра в серый."""
        for v in g["vertices"]:
            if v["name"] in removed:
                v["background"] = Palette.V_REMOVED_BG
                v["border"] = Palette.V_REMOVED_BORDER
                v["color"] = Palette.V_REMOVED_TEXT
        nbi = {i: v["name"] for i, v in enumerate(g["vertices"])}
        for e in g["edges"]:
            u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
            if u in removed or w in removed:
                e["color"] = Palette.E_REMOVED
                e["background"] = Palette.E_REMOVED
                e["lineWidth"] = Palette.LW_THIN

    def _base() -> dict[str, Any]:
        g = reset_colors(graph)
        for e in g["edges"]:                      # живые рёбра — чёрные
            e["color"] = Palette.E_BLACK
            e["background"] = Palette.E_BLACK
        _grey_out(g)
        return g

    rec = StepRecorder(base_dir, name)
    rec.add(_base(), "Инициализация",
            annotations=["Помеченное дерево; код Прюфера пуст"])

    while len(names) - len(removed) > 2:
        leaf = min(n for n in names
                   if n not in removed and len(neigh[n] - removed) == 1)
        parent = next(iter(neigh[leaf] - removed))
        code.append(parent)

        g = _base()
        color_vertex(g, leaf, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        color_vertex(g, parent, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
        color_edge(g, leaf, parent, Palette.E_ACTIVE, Palette.LW_THICK)
        rec.add(g, f"Удаляем лист {leaf}",
                annotations=[f"Минимальный лист: {leaf}, его сосед: {parent}",
                             "Код: (" + ", ".join(code) + ")"])
        removed.add(leaf)

    g = _base()
    for n in names:
        if n not in removed:
            color_vertex(g, n, Palette.V_FINAL_BG, Palette.V_FINAL_BORDER)
    rec.add(g, "Готово",
            annotations=["Осталось две вершины — стоп",
                         "Код Прюфера: (" + ", ".join(code) + ")"])
    return rec.finish()


def run_kruskal(graph: dict[str, Any], base_dir: Path, name: str, **_: Any) -> list[dict[str, Any]]:
    """Алгоритм Краскала (минимальное остовное дерево, через DSU)."""
    names, _adj = _adjacency(graph)
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}
    edges: list[tuple[float, str, str]] = []
    for e in graph["edges"]:
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        wt = _parse_weight(e.get("weight", "")) or 0.0
        edges.append((wt, u, w))
    edges.sort()

    parent = {n: n for n in names}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=["Рёбра отсортированы по весу"])

    total = 0.0
    for wt, u, w in edges:
        ru, rw = find(u), find(w)
        if ru == rw:
            color_edge(g, u, w, "#e0e0e0", Palette.LW_NORMAL)
            rec.add(g, f"Пропуск {u}—{w}", annotations=[f"Вес {_fmt(wt)}: образует цикл"])
            continue
        parent[ru] = rw
        total += wt
        color_edge(g, u, w, Palette.E_TREE, Palette.LW_THICK)
        color_vertex(g, u, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        color_vertex(g, w, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        rec.add(g, f"Добавляем {u}—{w}",
                annotations=[f"Вес = {_fmt(wt)}", f"Сумма = {_fmt(total)}"])

    rec.add(g, "Остов построен", annotations=[f"Суммарный вес = {_fmt(total)}"])
    return rec.finish()


def run_topsort(graph: dict[str, Any], base_dir: Path, name: str, **_: Any) -> list[dict[str, Any]]:
    """Топологическая сортировка (алгоритм Кана)."""
    from collections import deque

    names, adj = _adjacency(graph)
    indeg = {n: 0 for n in names}
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}
    for e in graph["edges"]:
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        indeg[w] += 1

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    queue = deque(sorted(n for n in names if indeg[n] == 0))
    for n in queue:
        color_vertex(g, n, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
    rec.add(g, "Инициализация",
            annotations=["В очередь — вершины с нулевой полустепенью захода"])

    order: list[str] = []
    while queue:
        u = queue.popleft()
        order.append(u)
        color_vertex(g, u, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        for w, _ in sorted(adj[u]):
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
                color_vertex(g, w, Palette.V_QUEUE_BG, Palette.V_QUEUE_BORDER)
        rec.add(g, f"Извлекаем {u}", annotations=[f"Порядок: {', '.join(order)}"])

    rec.add(g, "Готово", annotations=[f"Топологический порядок: {', '.join(order)}"])
    return rec.finish()


def run_ford_fulkerson(
    graph: dict[str, Any], source: str, sink: str, base_dir: Path, name: str
) -> list[dict[str, Any]]:
    """Алгоритм Форда—Фалкерсона (макс. поток) с поиском пути в ширину.

    На каждом шаге показывается дополняющий путь и остаточная сеть.
    Подпись ребра — «f/σ» (поток / пропускная способность).
    """
    from collections import deque

    names, _adj = _adjacency(graph)
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}

    # Пропускные способности и поток по ориентированным рёбрам.
    cap: dict[tuple[str, str], float] = {}
    base_edges: list[tuple[str, str]] = []
    for e in graph["edges"]:
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        c = _parse_weight(e.get("weight", "")) or 0.0
        cap[(u, w)] = cap.get((u, w), 0.0) + c
        base_edges.append((u, w))
    flow: dict[tuple[str, str], float] = {(u, w): 0.0 for (u, w) in base_edges}

    # Остаточная сеть: residual[(u,w)] — остаточная пропускная способность.
    residual: dict[tuple[str, str], float] = {}
    for (u, w), c in cap.items():
        residual[(u, w)] = c
        residual.setdefault((w, u), 0.0)

    def snapshot(highlight_path: Optional[list[str]] = None) -> dict[str, Any]:
        """Создаёт окрашенный граф с подписями f/σ и подсветкой пути."""
        g = copy.deepcopy(graph)
        for v in g["vertices"]:
            v["background"] = Palette.V_IDLE_BG
            v["border"] = Palette.V_IDLE_BORDER
        color_vertex(g, source, Palette.V_FINAL_BG, Palette.V_FINAL_BORDER)
        color_vertex(g, sink, Palette.V_FINAL_BG, Palette.V_FINAL_BORDER)
        path_edges = set()
        if highlight_path:
            for a, b in zip(highlight_path, highlight_path[1:]):
                path_edges.add((a, b))
        for e in g["edges"]:
            u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
            f = flow.get((u, w), 0.0)
            c = cap.get((u, w), 0.0)
            e["weight"] = f"{_fmt(f)}/{_fmt(c)}"
            if (u, w) in path_edges:
                e["color"] = e["background"] = Palette.E_ACTIVE
                e["lineWidth"] = Palette.LW_THICK
            elif f > 0:
                e["color"] = e["background"] = Palette.E_TREE
                e["lineWidth"] = Palette.LW_THICK
            else:
                e["color"] = e["background"] = Palette.E_BLACK
                e["lineWidth"] = Palette.LW_NORMAL
        return g

    rec = StepRecorder(base_dir, name)
    rec.add(snapshot(), "Инициализация",
            annotations=["∀e: f(e)=0", "Подпись ребра: f/σ"])

    def find_path() -> Optional[list[str]]:
        """BFS по остаточной сети (Эдмондс—Карп)."""
        parent: dict[str, Optional[str]] = {source: None}
        q = deque([source])
        while q:
            u = q.popleft()
            for w in names:
                if w not in parent and residual.get((u, w), 0.0) > 1e-9:
                    parent[w] = u
                    if w == sink:
                        path = [sink]
                        while parent[path[-1]] is not None:
                            path.append(parent[path[-1]])  # type: ignore[arg-type]
                        return list(reversed(path))
                    q.append(w)
        return None

    max_flow = 0.0
    iteration = 0
    while True:
        path = find_path()
        if path is None:
            break
        iteration += 1
        # пропускная способность пути = min остаточной
        bottleneck = min(residual[(a, b)] for a, b in zip(path, path[1:]))
        rec.add(snapshot(path), f"Дополняющий путь №{iteration}",
                annotations=[" → ".join(path), f"min остаточной = {_fmt(bottleneck)}"])
        # увеличиваем поток вдоль пути
        for a, b in zip(path, path[1:]):
            residual[(a, b)] -= bottleneck
            residual[(b, a)] = residual.get((b, a), 0.0) + bottleneck
            if (a, b) in flow:
                flow[(a, b)] += bottleneck
            elif (b, a) in flow:
                flow[(b, a)] -= bottleneck  # отмена потока по обратному ребру
        max_flow += bottleneck
        rec.add(snapshot(), f"Поток увеличен на {_fmt(bottleneck)}",
                annotations=[f"|f| = {_fmt(max_flow)}"])

    # Минимальный разрез: достижимые из S в остаточной сети.
    reachable = set()
    q = deque([source])
    reachable.add(source)
    while q:
        u = q.popleft()
        for w in names:
            if w not in reachable and residual.get((u, w), 0.0) > 1e-9:
                reachable.add(w)
                q.append(w)
    cut = [f"{u}→{w}" for (u, w) in cap if u in reachable and w not in reachable and cap[(u, w)] > 0]
    rec.add(snapshot(), "Максимальный поток найден",
            annotations=[f"|f|_max = {_fmt(max_flow)}",
                         "Мин. разрез: " + (", ".join(cut) if cut else "—")])
    return rec.finish()


def _fmt(x: float) -> str:
    """Аккуратное форматирование числа: целые без дробной части, ∞ как ∞."""
    if x == math.inf:
        return "∞"
    if x == -math.inf:
        return "−∞"
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


# Диспетчер: имя алгоритма → функция
ALGORITHMS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "dfs": run_dfs,
    "bfs": run_bfs,
    "dijkstra": run_dijkstra,
    "bellman_ford": run_bellman_ford,
    "prim": run_prim,
    "kruskal": run_kruskal,
    "topsort": run_topsort,
    "ford_fulkerson": run_ford_fulkerson,
}


# =============================================================================
# Дополнительные алгоритмы (SCC Косарайю, мосты, паросочетание Куна)
# =============================================================================
_COMP_COLORS = [
    ("#4caf50", "#388e3c"), ("#2196f3", "#1565c0"), ("#ff9800", "#e65100"),
    ("#9c27b0", "#6a1b9a"), ("#00bcd4", "#00838f"), ("#e91e63", "#ad1457"),
]


def run_kosaraju(graph, base_dir, name, **_):
    """Компоненты сильной связности (алгоритм Косарайю). Каждая компонента —
    своим цветом."""
    names, adj = _adjacency(graph)
    visited, order = set(), []

    def dfs1(s):
        stack = [(s, iter(adj[s]))]
        visited.add(s)
        while stack:
            u, it = stack[-1]
            for w, _ in it:
                if w not in visited:
                    visited.add(w)
                    stack.append((w, iter(adj[w])))
                    break
            else:
                order.append(u)
                stack.pop()

    for n in names:
        if n not in visited:
            dfs1(n)

    radj = {n: [] for n in names}
    for u in names:
        for w, _ in adj[u]:
            radj[w].append(u)

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=["Алгоритм Косарайю: 2 обхода DFS"])

    assigned, ci = {}, 0
    for s in reversed(order):
        if s in assigned:
            continue
        comp, st = [], [s]
        while st:
            u = st.pop()
            if u in assigned:
                continue
            assigned[u] = ci
            comp.append(u)
            for w in radj[u]:
                if w not in assigned:
                    st.append(w)
        bg, bd = _COMP_COLORS[ci % len(_COMP_COLORS)]
        for u in comp:
            color_vertex(g, u, bg, bd)
        for u in comp:
            for w, _ in adj[u]:
                if assigned.get(w) == ci:
                    color_edge(g, u, w, bg, Palette.LW_THICK)
        rec.add(g, f"Компонента {ci + 1}: {{{', '.join(comp)}}}",
                annotations=[f"Найдена компонента сильной связности №{ci + 1}"])
        ci += 1

    rec.add(g, "Готово", annotations=[f"Всего компонент: {ci}"])
    return rec.finish()


def run_bridges(graph, base_dir, name, **_):
    """Поиск мостов (DFS, времена входа/функция low). Мосты — красным."""
    names, adj = _adjacency(graph)
    tin, low, visited, bridges = {}, {}, set(), []
    timer = [0]

    def dfs(start):
        stack = [(start, None, iter(adj[start]))]
        visited.add(start)
        tin[start] = low[start] = timer[0]
        timer[0] += 1
        while stack:
            u, parent, it = stack[-1]
            advanced = False
            for w, _ in it:
                if w == parent:
                    continue
                if w in visited:
                    low[u] = min(low[u], tin[w])
                else:
                    visited.add(w)
                    tin[w] = low[w] = timer[0]
                    timer[0] += 1
                    stack.append((w, u, iter(adj[w])))
                    advanced = True
                    break
            if not advanced:
                stack.pop()
                if stack:
                    pu = stack[-1][0]
                    low[pu] = min(low[pu], low[u])
                    if low[u] > tin[pu]:
                        bridges.append((pu, u))

    for n in names:
        if n not in visited:
            dfs(n)

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=["Поиск мостов: DFS + функция low"])
    for i, (u, w) in enumerate(bridges, 1):
        color_edge(g, u, w, "#e53935", Palette.LW_THICK)
        color_vertex(g, u, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        color_vertex(g, w, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        rec.add(g, f"Мост {i}: ребро {u}\u2013{w}",
                annotations=[f"low({w}) > tin({u}) \u21d2 ребро {u}\u2013{w} — мост"])
    rec.add(g, "Готово", annotations=[f"Мостов найдено: {len(bridges)}"])
    return rec.finish()


def run_matching(graph, base_dir, name, **_):
    """Наибольшее паросочетание в двудольном графе (алгоритм Куна)."""
    names, adj = _adjacency(graph)
    color = {}
    for s in names:
        if s in color:
            continue
        color[s] = 0
        q = [s]
        while q:
            u = q.pop()
            for w, _ in adj[u]:
                if w not in color:
                    color[w] = color[u] ^ 1
                    q.append(w)
    left = [n for n in names if color.get(n, 0) == 0]
    match = {}

    def kuhn(u, used):
        for w, _ in adj[u]:
            if w in used:
                continue
            used.add(w)
            if w not in match or kuhn(match[w], used):
                match[w] = u
                return True
        return False

    rec = StepRecorder(base_dir, name)
    g = reset_colors(graph)
    rec.add(g, "Инициализация", annotations=["Двудольный граф; алгоритм Куна"])
    for u in left:
        kuhn(u, set())
        g = reset_colors(graph)
        for r, l in match.items():
            color_edge(g, l, r, Palette.E_TREE, Palette.LW_THICK)
            color_vertex(g, l, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
            color_vertex(g, r, Palette.V_DONE_BG, Palette.V_DONE_BORDER)
        color_vertex(g, u, Palette.V_ACTIVE_BG, Palette.V_ACTIVE_BORDER)
        rec.add(g, f"Насыщаем {u}", annotations=[f"Размер паросочетания: {len(match)}"])
    g = reset_colors(graph)
    for r, l in match.items():
        color_edge(g, l, r, Palette.E_TREE, Palette.LW_THICK)
        color_vertex(g, l, Palette.V_FINAL_BG, Palette.V_FINAL_BORDER)
        color_vertex(g, r, Palette.V_FINAL_BG, Palette.V_FINAL_BORDER)
    rec.add(g, "Готово", annotations=[f"Наибольшее паросочетание: {len(match)}"])
    return rec.finish()
