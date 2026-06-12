#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_fixes.py — генерация исправленных фигур и пошаговых серий для project7.

Покрывает:
  * лек. 2  — топсорт: новые шаги со стеком сбоку, без дублей, рёбра меняются;
  * лек. 3  — Флойд—Уоршелл: шаги на графе (a,b,c,d) + согласованные матрицы;
  * лек. 4  — мосты: шаги лекционного метода (ориентация → инверсия → DFS);
  * лек. 5  — Косарайю (чистый граф без графа Герца, стек сбоку), Флёри,
              списки инцидентности (перенумерация 1..6 -> A..K), задачи;
  * лек. 6  — гамильтонов путь (т. Дирака) с панелью последовательности,
              задачи (Прюфер / де Брёйн / Дирак);
  * лек. 7  — Прим: явные веса, шаги; новая задача;
  * лек. 8  — Краскал: явные веса, шаги; хорды/остов (2 рисунка); новая задача;
  * лек. 9  — двудольные примеры (раскраска долей), паросочетания (новые
              рисунки), шаги алгоритма паросочетания со «стрелками туда-обратно»,
              пример потока по путям; задача 8;
  * лек. 10 — Форд—Фалкерсон: сеть с фиксированными σ, шаги.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import graph_engine as ge
from graph_engine import Palette as P

HERE = Path(__file__).parent
FIG = HERE.parent / "figures"

# Цвета
BLUE_BG, BLUE_BD = "#bbdefb", "#1565c0"      # доля 1 / в пути
ORNG_BG, ORNG_BD = "#ffe0b2", "#e65100"      # доля 2
RED = "#e53935"
GREEN = "#4caf50"
LIGHT = "#b39ddb"                            # «полупрозрачные» добавленные рёбра
GRAY = "#c4c4c4"
STACK_BG, STACK_BD = "#ede7f6", "#7b1fa2"

VSTYLE = dict(radius=20, background="#ffffff", fontSize=18,
              color="#000000", border="#000000")
ESTYLE = dict(controlStep=0, fontSize=18, lineWidth=2,
              background="#000000", color="#000000")


def V(name, x, y, **kw):
    d = {"x": x, "y": y, "name": name, **VSTYLE}
    d.update(kw)
    return d


def E(i, j, w="", directed=False, **kw):
    d = {"vertex1": i, "vertex2": j, "weight": str(w),
         "isDirected": directed, **ESTYLE}
    d.update(kw)
    return d


def T(x, y, value, width=None, color="#000000", bg="#ffffff", bd="#000000",
      fs=18):
    return {"x": x, "y": y, "value": value,
            "width": width or max(40, 11 * len(value)), "height": 26,
            "fontSize": fs, "background": bg, "color": color, "border": bd}


def G(vertices, edges, texts=None):
    return {"x0": 0, "y0": 0, "vertices": vertices, "edges": edges,
            "texts": texts or []}


def names_of(g):
    return [v["name"] for v in g["vertices"]]


def idx_of(g):
    return {v["name"]: i for i, v in enumerate(g["vertices"])}


def vset(g, name, bg, bd, col="#000000"):
    for v in g["vertices"]:
        if v["name"] == name:
            v["background"], v["border"], v["color"] = bg, bd, col


def eset(g, u, w, color, lw=2.0, directed_only=False):
    nm = names_of(g)
    for e in g["edges"]:
        a, b = nm[e["vertex1"]], nm[e["vertex2"]]
        if (a, b) == (u, w) or (not directed_only and not e["isDirected"]
                                and (a, b) == (w, u)):
            e["color"] = e["background"] = color
            e["lineWidth"] = lw
            return


def eall(g, color="#000000", lw=2.0):
    for e in g["edges"]:
        e["color"] = e["background"] = color
        e["lineWidth"] = lw


def save_render(g, path_graph, path_pdf=None):
    path_graph = Path(path_graph)
    ge.save_graph(g, path_graph)
    ge.render_graph(g, path_pdf or path_graph.with_suffix(".pdf"))


def render_series(folder: Path, name: str, frames: list[dict]):
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob(f"{name}-*.graph")) + list(folder.glob(f"{name}-*.pdf")):
        old.unlink()
    for n, g in enumerate(frames):
        save_render(g, folder / f"{name}-{n}.graph")
    print(f"  {folder.relative_to(HERE)}/{name}: {len(frames)} кадров")


def stack_panel(entries_bottom_to_top, x, y_top, title="Стек"):
    """Панель стека: верх стека сверху."""
    texts = [T(x, y_top, title + ":", width=110, bd="#ffffff")]
    for k, val in enumerate(reversed(entries_bottom_to_top)):
        texts.append(T(x, y_top + 36 * (k + 1), val, width=110,
                       bg=STACK_BG, bd=STACK_BD))
    return texts


# =============================================================================
# ЛЕКЦИЯ 2 — Топологическая сортировка
# =============================================================================
def lec02_topsort():
    pos = {"A": (80, 50), "B": (330, 50), "C": (50, 280),
           "D": (380, 270), "E": (200, 400)}
    nm = ["A", "B", "C", "D", "E"]
    base_edges = [("A", "B"), ("C", "A"), ("C", "D"), ("C", "E"),
                  ("D", "A"), ("E", "D"), ("E", "B")]
    ix = {n: i for i, n in enumerate(nm)}

    def fresh():
        return G([V(n, *pos[n]) for n in nm],
                 [E(ix[u], ix[w], directed=True) for u, w in base_edges])

    # сохранить исходный граф как статическую фигуру лекции
    save_render(fresh(), FIG / "topsort-initial.graph")

    PANEL_X, PANEL_Y = 560, 60
    frames = []

    def frame(g, stack, numbered=False):
        gg = copy.deepcopy(g)
        if numbered:
            entries = [f"{v} = {i + 1}" for i, v in enumerate(stack)]
        else:
            entries = list(stack)
        gg["texts"] = stack_panel(entries, PANEL_X, PANEL_Y)
        frames.append(gg)

    g = fresh()
    frame(g, [])                                            # шаг 0

    # Шаг I: серия DFS, тупиковые вершины в стек
    # DFS из A: A -> B
    vset(g, "A", BLUE_BG, BLUE_BD)
    vset(g, "B", P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
    eset(g, "A", "B", GREEN, 3.5)
    frame(g, [])                                            # шаг 1
    # B тупиковая -> стек
    vset(g, "B", P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    frame(g, ["B"])                                         # шаг 2
    # A тупиковая -> стек
    vset(g, "A", P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    frame(g, ["B", "A"])                                    # шаг 3
    # DFS из C: C -> D, D тупиковая
    vset(g, "C", BLUE_BG, BLUE_BD)
    vset(g, "D", P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    eset(g, "C", "D", GREEN, 3.5)
    frame(g, ["B", "A", "D"])                               # шаг 4
    # C -> E, E тупиковая
    vset(g, "E", P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    eset(g, "C", "E", GREEN, 3.5)
    frame(g, ["B", "A", "D", "E"])                          # шаг 5
    # C тупиковая — шаг I завершён
    vset(g, "C", P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    frame(g, ["B", "A", "D", "E", "C"])                     # шаг 6

    stack = ["B", "A", "D", "E", "C"]

    # Шаг II-а: нумерация по стеку + рефлексивные петли
    g2 = fresh()
    for v in nm:
        vset(g2, v, "#fff9c4", "#f9a825")
    for e in g2["edges"]:
        e["color"] = e["background"] = "#000000"
    for v in nm:
        g2["edges"].append(E(ix[v], ix[v], color=LIGHT, background=LIGHT,
                             lineWidth=2))
    frame(g2, stack, numbered=True)                         # шаг 7

    # Шаг II-б: дорисовываем недостающие рёбра (от большего к меньшему)
    g3 = copy.deepcopy(g2)
    have = set(base_edges)
    order = {v: i for i, v in enumerate(stack)}             # B=0 < A < D < E < C
    for hi in nm:
        for lo in nm:
            if hi != lo and order[hi] > order[lo] and (hi, lo) not in have:
                g3["edges"].append(E(ix[hi], ix[lo], directed=True,
                                     color=LIGHT, background=LIGHT,
                                     lineWidth=2))
    g3["texts"] = stack_panel([f"{v} = {i+1}" for i, v in enumerate(stack)],
                              PANEL_X, PANEL_Y)
    frames.append(g3)                                       # шаг 8

    render_series(HERE / "lec02" / "topsort", "topsort", frames)


# =============================================================================
# ЛЕКЦИЯ 3 — Флойд—Уоршелл (транзитивное замыкание): граф + матрицы
# =============================================================================
def lec03_floyd():
    pos = {"a": (0, 160), "b": (190, 20), "c": (400, 20), "d": (590, 160)}
    nm = ["a", "b", "c", "d"]
    ix = {n: i for i, n in enumerate(nm)}
    base = [("a", "b"), ("b", "c"), ("c", "d")]

    def fresh():
        return G([V(n, *pos[n]) for n in nm],
                 [E(ix[u], ix[w], directed=True) for u, w in base])

    # шаг 0 — исходный граф
    save_render(fresh(), FIG / "fw-step-0.graph")

    # шаг k=b: добавляется a->c
    g = fresh()
    vset(g, "b", P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
    eset(g, "a", "b", BLUE_BD, 3.0)
    eset(g, "b", "c", BLUE_BD, 3.0)
    g["edges"].append(E(ix["a"], ix["c"], directed=True, color=GREEN,
                        background=GREEN, lineWidth=3.5))
    save_render(g, FIG / "fw-step-1.graph")

    # шаг k=c: добавляются a->d и b->d
    g = fresh()
    g["edges"].append(E(ix["a"], ix["c"], directed=True, color=LIGHT,
                        background=LIGHT, lineWidth=2.5))
    vset(g, "c", P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
    g["edges"].append(E(ix["a"], ix["d"], directed=True, color=GREEN,
                        background=GREEN, lineWidth=3.5))
    g["edges"].append(E(ix["b"], ix["d"], directed=True, color=GREEN,
                        background=GREEN, lineWidth=3.5))
    save_render(g, FIG / "fw-step-2.graph")

    # итог: транзитивное замыкание
    g = fresh()
    for u, w in [("a", "c"), ("a", "d"), ("b", "d")]:
        g["edges"].append(E(ix[u], ix[w], directed=True, color=LIGHT,
                            background=LIGHT, lineWidth=2.5))
    save_render(g, FIG / "fw-step-3.graph")


# =============================================================================
# ЛЕКЦИЯ 4 — Мосты: лекционный метод (ориентация -> инверсия -> DFS)
# =============================================================================
def lec04_bridges():
    src = ge.load_graph(FIG / "p11-example-5.graph")
    nm = names_of(src)
    ix = idx_of(src)
    orient = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "B"),
              ("D", "F"), ("F", "H"), ("H", "I"), ("I", "J"), ("J", "K"),
              ("K", "L"), ("L", "M"), ("I", "F")]
    comps = [["A"], ["B", "C", "D", "E"], ["F", "H", "I"],
             ["J"], ["K"], ["L"], ["M"]]
    bridges = [("A", "B"), ("D", "F"), ("I", "J"), ("J", "K"),
               ("K", "L"), ("L", "M")]
    CC = [("#90caf9", "#1565c0"), ("#a5d6a7", "#2e7d32"),
          ("#ffcc80", "#e65100"), ("#ce93d8", "#6a1b9a"),
          ("#80deea", "#00838f"), ("#f48fb1", "#ad1457"),
          ("#fff59d", "#f9a825")]
    frames = []

    g0 = ge.reset_colors(src)
    eall(g0, "#000000", 2.0)
    frames.append(g0)                                       # 0: исходный

    g1 = G(copy.deepcopy(src["vertices"]),
           [E(ix[u], ix[w], directed=True, color=GREEN, background=GREEN,
              lineWidth=2.5) for u, w in orient])
    for v in g1["vertices"]:
        v["background"], v["border"], v["color"] = "#ffffff", "#000000", "#000000"
    frames.append(g1)                                       # 1: ориентация

    g2 = G(copy.deepcopy(g1["vertices"]),
           [E(ix[w], ix[u], directed=True, color=BLUE_BD, background=BLUE_BD,
              lineWidth=2.5) for u, w in orient])
    frames.append(g2)                                       # 2: инверсия

    g3 = copy.deepcopy(g2)
    eall(g3, GRAY, 1.5)
    for ci, comp in enumerate(comps):
        bg, bd = CC[ci % len(CC)]
        for v in comp:
            vset(g3, v, bg, bd)
        for u, w in orient:
            if u in comp and w in comp:
                eset(g3, w, u, bd, 3.0, directed_only=True)
    frames.append(g3)                                       # 3: компоненты

    g4 = ge.reset_colors(src)
    eall(g4, "#000000", 2.0)
    for ci, comp in enumerate(comps):
        bg, bd = CC[ci % len(CC)]
        for v in comp:
            vset(g4, v, bg, bd)
    for u, w in bridges:
        eset(g4, u, w, RED, 3.5)
    frames.append(g4)                                       # 4: мосты

    render_series(HERE / "lec04" / "bridges", "bridges", frames)


# =============================================================================
# ЛЕКЦИЯ 5 — Косарайю, Флёри, списки инцидентности, задачи
# =============================================================================
def lec05_kosaraju():
    # 1) дополняем лекционный рисунок ребром F->E (иначе {E,F} не КСС)
    full = ge.load_graph(FIG / "p12-example-1.graph")
    nmf = names_of(full)
    has_fe = any(nmf[e["vertex1"]] == "F" and nmf[e["vertex2"]] == "E"
                 for e in full["edges"])
    if not has_fe:
        i_f = next(i for i, v in enumerate(full["vertices"])
                   if v["name"] == "F" and v["x"] < -300)
        i_e = next(i for i, v in enumerate(full["vertices"])
                   if v["name"] == "E" and v["x"] < -300)
        full["edges"].append(E(i_f, i_e, directed=True))
        save_render(full, FIG / "p12-example-1.graph")

    # 2) чистый граф (без графа Герца) для шагов
    keep = [(v, i) for i, v in enumerate(full["vertices"]) if v["x"] < -250]
    old2new = {i: k for k, (_, i) in enumerate(keep)}
    main = G([copy.deepcopy(v) for v, _ in keep],
             [E(old2new[e["vertex1"]], old2new[e["vertex2"]], directed=True)
              for e in full["edges"]
              if e["vertex1"] in old2new and e["vertex2"] in old2new])
    save_render(ge.reset_colors(main) | {"texts": []}, FIG / "p12-scc-main.graph")
    main = ge.load_graph(FIG / "p12-scc-main.graph")

    PANEL_X, PANEL_Y = -250, 120
    stack = ["D", "F", "E", "J", "I", "H", "C", "B", "A"]   # снизу вверх
    comps = [["A", "B", "D"], ["C"], ["H", "I", "J"], ["E", "F"]]
    CC = [("#a5d6a7", "#2e7d32"), ("#90caf9", "#1565c0"),
          ("#ffcc80", "#e65100"), ("#ce93d8", "#6a1b9a")]
    frames = []

    g0 = ge.reset_colors(main)
    eall(g0, "#000000", 2.0)
    frames.append(g0)                                       # 0

    g1 = copy.deepcopy(g0)
    for v in names_of(main):
        vset(g1, v, P.V_DONE_BG, P.V_DONE_BORDER, "#ffffff")
    g1["texts"] = stack_panel(stack, PANEL_X, PANEL_Y)
    frames.append(g1)                                       # 1: шаг I

    ix = idx_of(main)
    nm = names_of(main)
    g2 = G(copy.deepcopy(main["vertices"]),
           [E(e["vertex2"], e["vertex1"], directed=True, color=BLUE_BD,
              background=BLUE_BD, lineWidth=2.5) for e in main["edges"]],
           stack_panel(stack, PANEL_X, PANEL_Y))
    frames.append(g2)                                       # 2: инверсия

    ginv = copy.deepcopy(g2)
    eall(ginv, GRAY, 1.5)
    rest = list(stack)
    for ci, comp in enumerate(comps):
        bg, bd = CC[ci]
        for v in comp:
            vset(ginv, v, bg, bd, "#000000")
        for e in main["edges"]:
            u, w = nm[e["vertex1"]], nm[e["vertex2"]]
            if u in comp and w in comp:
                eset(ginv, w, u, bd, 3.0, directed_only=True)
        rest = [v for v in rest if v not in comp]
        gg = copy.deepcopy(ginv)
        gg["texts"] = stack_panel(rest, PANEL_X, PANEL_Y)
        frames.append(gg)                                   # 3..6

    gf = ge.reset_colors(main)
    eall(gf, "#000000", 2.0)
    for ci, comp in enumerate(comps):
        bg, bd = CC[ci]
        for v in comp:
            vset(gf, v, bg, bd)
        for e in main["edges"]:
            u, w = nm[e["vertex1"]], nm[e["vertex2"]]
            if u in comp and w in comp:
                eset(gf, u, w, bd, 3.0, directed_only=True)
    frames.append(gf)                                       # 7: итог

    render_series(HERE / "lec05" / "kosaraju", "kosaraju", frames)


def lec05_fleury():
    src = ge.load_graph(FIG / "p14-example-1.graph")
    trail = [("B", "A"), ("A", "C"), ("C", "B"), ("B", "E"), ("E", "C"),
             ("C", "D"), ("D", "E"), ("E", "A"), ("A", "D")]
    cuts = [0, 3, 6, 9]
    frames = []
    for cut in cuts:
        g = ge.reset_colors(src)
        eall(g, "#000000", 2.0)
        for k, (u, w) in enumerate(trail[:cut], 1):
            nmg = names_of(g)
            for e in g["edges"]:
                a, b = nmg[e["vertex1"]], nmg[e["vertex2"]]
                if {a, b} == {u, w}:
                    e["color"] = e["background"] = GREEN
                    e["lineWidth"] = 3.5
                    e["weight"] = str(k)
        cur = "B" if cut == 0 else trail[cut - 1][1]
        vset(g, "B", BLUE_BG, BLUE_BD)          # старт
        vset(g, cur, P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
        frames.append(g)
    render_series(HERE / "lec05" / "fleury", "fleury", frames)


def lec05_misc():
    # перенумеровать вершины p14-example-2: 1..6 -> A,B,C,D,E,K
    g = ge.load_graph(FIG / "p14-example-2.graph")
    ren = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "K"}
    for v in g["vertices"]:
        v["name"] = ren.get(v["name"], v["name"])
    save_render(g, FIG / "p14-example-2.graph")

    # исправить опечатку в подписях p13-example-4, добавить подпись в -6
    g = ge.load_graph(FIG / "p13-example-4.graph")
    for t in g.get("texts", []):
        t["value"] = (t["value"].replace("эейлеров", "эйлеров")
                      .replace("полуэейлеров", "полуэйлеров"))
    save_render(g, FIG / "p13-example-4.graph")
    g = ge.load_graph(FIG / "p13-example-6.graph")
    if not g.get("texts"):
        xs = [v["x"] for v in g["vertices"]]
        ys = [v["y"] for v in g["vertices"]]
        g["texts"] = [T(min(xs) - 240, (min(ys) + max(ys)) // 2,
                        "Ни эйлеров,", bd="#ffffff"),
                      T(min(xs) - 240, (min(ys) + max(ys)) // 2 + 30,
                        "ни полуэйлеров", bd="#ffffff")]
    save_render(g, FIG / "p13-example-6.graph")

    # задача: эйлеровость (квадрат + диагональ)
    nm = ["A", "B", "C", "D"]
    pos = {"A": (0, 0), "B": (220, 0), "C": (220, 220), "D": (0, 220)}
    ix = {n: i for i, n in enumerate(nm)}
    g = G([V(n, *pos[n]) for n in nm],
          [E(ix[u], ix[w]) for u, w in
           [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C")]])
    save_render(g, FIG / "task-euler-1.graph")
    g2 = copy.deepcopy(g)
    for k, (u, w) in enumerate([("A", "B"), ("B", "C"), ("C", "D"),
                                ("D", "A"), ("A", "C")], 1):
        # порядок обхода A-B-C-D-A-C
        pass
    for k, (u, w) in enumerate([("A", "B"), ("B", "C"), ("C", "D"),
                                ("D", "A"), ("A", "C")], 1):
        eset(g2, u, w, GREEN, 3.0)
    for k, (u, w) in enumerate([("A", "B"), ("B", "C"), ("C", "D"),
                                ("D", "A"), ("A", "C")], 1):
        nmg = names_of(g2)
        for e in g2["edges"]:
            a, b = nmg[e["vertex1"]], nmg[e["vertex2"]]
            if {a, b} == {u, w}:
                e["weight"] = str(k)
    vset(g2, "A", BLUE_BG, BLUE_BD)
    vset(g2, "C", ORNG_BG, ORNG_BD)
    save_render(g2, FIG / "task-euler-2.graph")

    # задача: КСС (Косарайю)
    nm = ["A", "B", "C", "D", "E"]
    pos = {"A": (0, 0), "B": (160, 110), "C": (0, 220),
           "D": (360, 110), "E": (530, 110)}
    ix = {n: i for i, n in enumerate(nm)}
    arcs = [("A", "B"), ("B", "C"), ("C", "A"), ("B", "D"),
            ("D", "E"), ("E", "D")]
    g = G([V(n, *pos[n]) for n in nm],
          [E(ix[u], ix[w], directed=True) for u, w in arcs])
    save_render(g, FIG / "task-scc-1.graph")
    g2 = copy.deepcopy(g)
    for v in ["A", "B", "C"]:
        vset(g2, v, "#a5d6a7", "#2e7d32")
    for v in ["D", "E"]:
        vset(g2, v, "#90caf9", "#1565c0")
    for u, w in [("A", "B"), ("B", "C"), ("C", "A")]:
        eset(g2, u, w, "#2e7d32", 3.0, directed_only=True)
    for u, w in [("D", "E"), ("E", "D")]:
        eset(g2, u, w, "#1565c0", 3.0, directed_only=True)
    save_render(g2, FIG / "task-scc-2.graph")


# =============================================================================
# ЛЕКЦИЯ 6 — Гамильтонов путь (Дирак), задачи
# =============================================================================
def lec06_hamilton():
    src = ge.load_graph(FIG / "p15-example-4.graph")
    nm = names_of(src)
    ix = idx_of(src)
    if not any({nm[e["vertex1"]], nm[e["vertex2"]]} == {"B", "E"}
               for e in src["edges"]):
        src["edges"].append(E(ix["B"], ix["E"]))
    save_render(ge.reset_colors(src) | {"texts": []},
                FIG / "p15-example-4b.graph")
    src = ge.load_graph(FIG / "p15-example-4b.graph")
    eall(src, "#000000", 2.0)
    xs = [v["x"] for v in src["vertices"]]
    ys = [v["y"] for v in src["vertices"]]
    ty = max(ys) + 110
    tx = (min(xs) + max(xs)) // 2 - 170

    frames = []
    # кадр 0: последовательность E,A,B,D,F,C; пары-рёбра синие, несмежная пара красная
    g = copy.deepcopy(src)
    for u, w in [("A", "B"), ("B", "D"), ("D", "F"), ("F", "C")]:
        eset(g, u, w, BLUE_BD, 3.0)
    g["edges"].append(E(ix["E"], ix["A"], color=RED, background=RED,
                        lineWidth=3.0))
    g["texts"] = [T(tx, ty, "Последовательность: E, A, B, D, F, C",
                    bd="#ffffff"),
                  T(tx, ty + 32, "Несмежная пара: (E, A)", color=RED,
                    bd="#ffffff")]
    frames.append(g)

    # кадр 1: поворот — рёбра E-B и A-D зелёные, отрезок A,B оранжевый
    g = copy.deepcopy(src)
    for u, w in [("B", "D"), ("D", "F"), ("F", "C")]:
        eset(g, u, w, BLUE_BD, 3.0)
    g["edges"].append(E(ix["E"], ix["A"], color=RED, background=RED,
                        lineWidth=2.0))
    eset(g, "B", "E", GREEN, 3.5)
    eset(g, "A", "D", GREEN, 3.5)
    vset(g, "A", P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
    vset(g, "B", P.V_ACTIVE_BG, P.V_ACTIVE_BORDER, "#ffffff")
    g["texts"] = [T(tx, ty, "Поворот: j = 3,  v_j = B,  v_{j+1} = D",
                    bd="#ffffff"),
                  T(tx, ty + 32, "E–B и A–D есть в графе → переворачиваем (A, B)",
                    bd="#ffffff")]
    frames.append(g)

    # кадр 2: результат — гамильтонов путь E,B,A,D,F,C
    g = copy.deepcopy(src)
    for u, w in [("E", "B"), ("B", "A"), ("A", "D"), ("D", "F"), ("F", "C")]:
        eset(g, u, w, GREEN, 3.5)
    vset(g, "E", BLUE_BG, BLUE_BD)
    vset(g, "C", ORNG_BG, ORNG_BD)
    g["texts"] = [T(tx, ty, "Гамильтонов путь: E, B, A, D, F, C",
                    bd="#ffffff")]
    frames.append(g)

    # кадр 3: замыкание C-E — гамильтонов цикл
    g = copy.deepcopy(src)
    for u, w in [("E", "B"), ("B", "A"), ("A", "D"), ("D", "F"), ("F", "C"),
                 ("C", "E")]:
        eset(g, u, w, GREEN, 3.5)
    g["texts"] = [T(tx, ty, "C и E смежны → гамильтонов цикл", bd="#ffffff")]
    frames.append(g)

    render_series(HERE / "lec06" / "hamilton", "hamilton", frames)


def lec06_tasks():
    # задача Прюфера: дерево 1..6
    nm = ["1", "2", "3", "4", "5", "6"]
    pos = {"1": (0, 0), "2": (0, 200), "3": (170, 100), "4": (370, 100),
           "5": (540, 0), "6": (540, 200)}
    ix = {n: i for i, n in enumerate(nm)}
    g = G([V(n, *pos[n]) for n in nm],
          [E(ix[u], ix[w]) for u, w in
           [("1", "3"), ("2", "3"), ("3", "4"), ("4", "5"), ("4", "6")]])
    save_render(g, FIG / "task-pruefer-1.graph")

    # задача де Брёйна: B({0,1},2) с вершинами-словами длины 1
    g = G([V("0", 0, 90), V("1", 300, 90)],
          [E(0, 0, w="00"), E(0, 1, w="01", directed=True),
           E(1, 0, w="10", directed=True), E(1, 1, w="11")])
    save_render(g, FIG / "task-debruijn-1.graph")

    # задача Дирака: K5 без AD и BE
    nm = ["A", "B", "C", "D", "E"]
    pos = {"A": (170, 0), "B": (340, 120), "C": (275, 320),
           "D": (65, 320), "E": (0, 120)}
    ix = {n: i for i, n in enumerate(nm)}
    edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "A"),
             ("A", "C"), ("B", "D"), ("C", "E")]
    g = G([V(n, *pos[n]) for n in nm], [E(ix[u], ix[w]) for u, w in edges])
    save_render(g, FIG / "task-dirac-1.graph")
    g2 = copy.deepcopy(g)
    for u, w in [("A", "B"), ("B", "D"), ("D", "C"), ("C", "E"), ("E", "A")]:
        eset(g2, u, w, GREEN, 3.5)
    save_render(g2, FIG / "task-dirac-2.graph")


# =============================================================================
# ЛЕКЦИЯ 7 — Прим (лекционный граф с явными весами) + задача
# =============================================================================
PRIM_W = {("I", "J"): 3, ("D", "I"): 1, ("I", "F"): 2, ("A", "D"): 4,
          ("D", "H"): 5, ("D", "C"): 7, ("B", "C"): 1, ("E", "C"): 8,
          ("A", "B"): 6, ("B", "D"): 9, ("F", "H"): 6, ("D", "F"): 5}


def lec07_prim():
    g = ge.load_graph(FIG / "p19-prim-example-1.graph")
    nm = names_of(g)
    for e in g["edges"]:
        u, w = nm[e["vertex1"]], nm[e["vertex2"]]
        wt = PRIM_W.get((u, w)) or PRIM_W.get((w, u))
        e["weight"] = str(wt)
    save_render(g, FIG / "p19-prim-example-1.graph")
    out = HERE / "lec07" / "prim"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("prim-*.graph")) + list(out.glob("prim-*.pdf")):
        old.unlink()
    steps = ge.run_prim(g, "J", out, "prim")
    print(f"  lec07/prim: {len(steps)} шагов;",
          " | ".join(s["title"] for s in steps))

    # задача 6: новый граф
    nm = ["A", "B", "C", "D", "E", "F"]
    pos = {"A": (0, 90), "B": (200, 0), "C": (140, 230), "D": (420, 0),
           "E": (360, 180), "F": (560, 120)}
    ix = {n: i for i, n in enumerate(nm)}
    tw = {("A", "B"): 4, ("A", "C"): 2, ("B", "C"): 5, ("B", "D"): 10,
          ("C", "E"): 3, ("E", "D"): 6, ("E", "F"): 7, ("D", "F"): 11}
    gt = G([V(n, *pos[n]) for n in nm],
           [E(ix[u], ix[w], w=wt) for (u, w), wt in tw.items()])
    save_render(gt, FIG / "task-prim-1.graph")
    out = HERE / "lec07" / "prim_task"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("*.graph")) + list(out.glob("*.pdf")):
        old.unlink()
    steps = ge.run_prim(ge.load_graph(FIG / "task-prim-1.graph"), "A",
                        out, "primt")
    print(f"  lec07/prim_task: {len(steps)} шагов;",
          " | ".join(s["title"] for s in steps))


# =============================================================================
# ЛЕКЦИЯ 8 — Краскал (явные веса) + хорды/остов + задача
# =============================================================================
KRUSKAL_W = {("J", "I"): 1, ("B", "C"): 2, ("A", "D"): 3, ("H", "D"): 4,
             ("A", "F"): 5, ("D", "E"): 6, ("J", "D"): 7, ("B", "D"): 8,
             ("E", "C"): 9, ("B", "E"): 10, ("A", "B"): 11, ("F", "H"): 12,
             ("H", "I"): 13, ("E", "J"): 14}


def lec08_kruskal():
    g = ge.load_graph(FIG / "p20-kraskal-example-1.graph")
    nm = names_of(g)
    for e in g["edges"]:
        u, w = nm[e["vertex1"]], nm[e["vertex2"]]
        wt = KRUSKAL_W.get((u, w)) or KRUSKAL_W.get((w, u))
        e["weight"] = str(wt)
    save_render(g, FIG / "p20-kraskal-example-1.graph")
    out = HERE / "lec08" / "kruskal"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("kruskal-*.graph")) + list(out.glob("kruskal-*.pdf")):
        old.unlink()
    steps = ge.run_kruskal(g, out, "kruskal")
    print(f"  lec08/kruskal: {len(steps)} шагов;",
          " | ".join(s["title"] for s in steps))

    # хорды: два рисунка (граф с остовом и хордами / только остов)
    src = ge.load_graph(FIG / "p20-glavnie-circle-example-1.graph")
    tree = [("B", "C"), ("A", "D"), ("B", "D"), ("A", "F"),
            ("H", "D"), ("H", "I"), ("J", "I"), ("D", "E")]
    chords = [("A", "B"), ("J", "D"), ("B", "E"), ("F", "H"),
              ("E", "J"), ("E", "C")]
    g1 = ge.reset_colors(src)
    for u, w in tree:
        eset(g1, u, w, GREEN, 3.5)
    for u, w in chords:
        eset(g1, u, w, RED, 2.0)
    save_render(g1, FIG / "p20-chords-graph.graph")
    nmg = names_of(src)
    ixg = idx_of(src)
    g2 = G(copy.deepcopy(src["vertices"]),
           [E(ixg[u], ixg[w], color=GREEN, background=GREEN, lineWidth=3.0)
            for u, w in tree])
    save_render(g2, FIG / "p20-chords-tree.graph")

    # задача 7: новый граф (7 вершин)
    nm = ["A", "B", "C", "D", "E", "F", "G"]
    pos = {"A": (0, 110), "B": (170, 0), "C": (360, 0), "D": (170, 230),
          "E": (360, 140), "F": (360, 300), "G": (540, 150)}
    ix = {n: i for i, n in enumerate(nm)}
    tw = {("A", "B"): 7, ("A", "D"): 5, ("B", "C"): 8, ("B", "D"): 9,
          ("B", "E"): 7, ("C", "E"): 5, ("D", "E"): 15, ("D", "F"): 6,
          ("E", "F"): 8, ("E", "G"): 9, ("F", "G"): 11}
    gt = G([V(n, *pos[n]) for n in nm],
           [E(ix[u], ix[w], w=wt) for (u, w), wt in tw.items()])
    save_render(gt, FIG / "task-kruskal-1.graph")
    out = HERE / "lec08" / "kruskal_task"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("*.graph")) + list(out.glob("*.pdf")):
        old.unlink()
    steps = ge.run_kruskal(ge.load_graph(FIG / "task-kruskal-1.graph"),
                           out, "kruskalt")
    print(f"  lec08/kruskal_task: {len(steps)} шагов;",
          " | ".join(s["title"] for s in steps))


# =============================================================================
# ЛЕКЦИЯ 9 — двудольность, паросочетания, поток
# =============================================================================
def _bicolor(path, part1, part2, conflict_edge=None, drop_edges=None):
    g = ge.load_graph(path)
    nm = names_of(g)
    if drop_edges:
        g["edges"] = [e for e in g["edges"]
                      if {nm[e["vertex1"]], nm[e["vertex2"]]} not in
                      [set(p) for p in drop_edges]]
    eall(g, "#000000", 2.0)
    for v in part1:
        vset(g, v, BLUE_BG, BLUE_BD)
    for v in part2:
        vset(g, v, ORNG_BG, ORNG_BD)
    if conflict_edge:
        eset(g, *conflict_edge, RED, 3.5)
    save_render(g, path)


def lec09_bipartite():
    _bicolor(FIG / "p21-example-1.graph",
             ["1", "3", "4", "6", "9", "11"], ["2", "5", "7", "8", "10"])
    _bicolor(FIG / "p21-example-2.graph",
             ["1", "3", "6", "8", "9"], ["2", "4", "5", "7", "10"])
    _bicolor(FIG / "p21-example-3.graph", ["1", "3"], ["2"],
             conflict_edge=("3", "1"))
    # чётный цикл C8 (убираем «диагонали», ломавшие двудольность)
    _bicolor(FIG / "p21-example-4.graph",
             ["1", "3", "6", "8"], ["2", "4", "5", "7"],
             drop_edges=[("1", "5"), ("2", "6"), ("3", "7"), ("4", "8")])
    # нечётный цикл C7: 1-2-3-4-8-7-6-1
    _bicolor(FIG / "p21-example-5.graph",
             ["1", "3", "8"], ["2", "4", "7", "6"],
             conflict_edge=("1", "6"))


def lec09_matching_small():
    """Четыре маленьких примера паросочетаний на пути 1-2-3-4."""
    pos = {"1": (0, 0), "2": (200, 0), "3": (0, 180), "4": (200, 180)}
    path_edges = [("1", "2"), ("2", "3"), ("3", "4")]

    def mk(fname, matched, label):
        nm = ["1", "2", "3", "4"]
        ix = {n: i for i, n in enumerate(nm)}
        g = G([V(n, *pos[n]) for n in nm],
              [E(ix[u], ix[w]) for u, w in path_edges],
              [T(-260, 70, label, bd="#ffffff")])
        sat = set()
        for u, w in matched:
            eset(g, u, w, GREEN, 4.0)
            sat |= {u, w}
        for v in sat:
            vset(g, v, "#c8e6c9", "#2e7d32")
        save_render(g, FIG / fname)

    mk("p22-example-1.graph", [("1", "2")], "не макс., не наиб.")
    mk("p22-example-2.graph", [("2", "3")], "макс., не наиб.")
    mk("p22-example-3.graph", [("1", "2"), ("3", "4")], "макс. и наиб.")
    mk("p22-example-4.graph", [("3", "4")], "не макс., не наиб.")


def lec09_matching_steps():
    src = ge.load_graph(FIG / "p22-example-5.graph")
    nm = names_of(src)
    ix = idx_of(src)
    V1, V2 = ["A", "B", "C", "D"], ["α", "β", "γ"]

    def base(matched, used_sf):
        """matched: список (v, w) v∈V1, w∈V2 — рёбра инвертированы (w->v),
        used_sf: использованные рёбра S->v и w->F (серые)."""
        g = G(copy.deepcopy(src["vertices"]), [], [])
        for v in V1:
            vset(g, v, BLUE_BG, BLUE_BD)
        for v in V2:
            vset(g, v, ORNG_BG, ORNG_BD)
        vset(g, "S", "#fff9c4", "#f9a825")
        vset(g, "F", "#fff9c4", "#f9a825")
        minv = {(v, w) for v, w in matched}
        for e in src["edges"]:
            u, w = nm[e["vertex1"]], nm[e["vertex2"]]
            if (u, w) in minv:                      # инвертируем: w -> u
                g["edges"].append(E(ix[w], ix[u], directed=True, color=GREEN,
                                    background=GREEN, lineWidth=3.5))
            elif (u, w) in used_sf:
                g["edges"].append(E(ix[u], ix[w], directed=True, color=GRAY,
                                    background=GRAY, lineWidth=1.5))
            else:
                g["edges"].append(E(ix[u], ix[w], directed=True))
        return g

    def hl(g, path):
        """подсветить путь оранжевым (рёбра между последовательными вершинами,
        в любом текущем направлении)."""
        nmg = names_of(g)
        for a, b in zip(path, path[1:]):
            for e in g["edges"]:
                u, w = nmg[e["vertex1"]], nmg[e["vertex2"]]
                if (u, w) == (a, b):
                    e["color"] = e["background"] = P.E_ACTIVE
                    e["lineWidth"] = 3.5
        return g

    frames = []
    frames.append(base([], set()))                                   # 0
    frames.append(hl(base([], set()), ["S", "B", "β", "F"]))         # 1
    st1, used1 = [("B", "β")], {("S", "B"), ("β", "F")}
    frames.append(base(st1, used1))                                  # 2
    frames.append(hl(base(st1, used1),
                     ["S", "C", "β", "B", "α", "F"]))                # 3
    st2 = [("C", "β"), ("B", "α")]
    used2 = used1 | {("S", "C"), ("α", "F")}
    frames.append(base(st2, used2))                                  # 4
    frames.append(hl(base(st2, used2),
                     ["S", "A", "β", "C", "γ", "F"]))                # 5
    st3 = [("A", "β"), ("B", "α"), ("C", "γ")]
    used3 = used2 | {("S", "A"), ("γ", "F")}
    frames.append(base(st3, used3))                                  # 6
    render_series(HERE / "lec09" / "matching", "matching", frames)

    # перекрасить сам лекционный рисунок (доли цветом)
    g = ge.reset_colors(src)
    eall(g, "#000000", 2.0)
    for v in V1:
        vset(g, v, BLUE_BG, BLUE_BD)
    for v in V2:
        vset(g, v, ORNG_BG, ORNG_BD)
    vset(g, "S", "#fff9c4", "#f9a825")
    vset(g, "F", "#fff9c4", "#f9a825")
    save_render(g, FIG / "p22-example-5.graph")

    # задача 8: условие (доли цветом) + решение
    m = ge.load_graph(FIG / "match-example.graph")
    eall(m, "#000000", 2.0)
    for v in ["a", "b", "c"]:
        vset(m, v, BLUE_BG, BLUE_BD)
    for v in ["x", "y", "z"]:
        vset(m, v, ORNG_BG, ORNG_BD)
    save_render(m, FIG / "match-example.graph")
    m2 = copy.deepcopy(m)
    for u, w in [("a", "y"), ("b", "x"), ("c", "z")]:
        eset(m2, u, w, GREEN, 4.0)
    save_render(m2, FIG / "task-matching-sol.graph")


FLOW_CAP = {("S", "A"): 2, ("S", "B"): 3, ("A", "C"): 1, ("A", "B"): 1,
            ("B", "D"): 4, ("D", "C"): 2, ("C", "F"): 3, ("D", "F"): 2}


def lec09_flow_example():
    src = ge.load_graph(FIG / "p23-example-1.graph")
    nm = names_of(src)
    # вписать пропускные способности в лекционный рисунок
    g0 = ge.reset_colors(src)
    eall(g0, "#000000", 2.0)
    for e in g0["edges"]:
        u, w = nm[e["vertex1"]], nm[e["vertex2"]]
        e["weight"] = str(FLOW_CAP[(u, w)])
    vset(g0, "S", "#fff9c4", "#f9a825")
    vset(g0, "F", "#fff9c4", "#f9a825")
    save_render(g0, FIG / "p23-example-1.graph")

    paths = [["S", "B", "D", "F"], ["S", "A", "C", "F"],
             ["S", "A", "B", "D", "C", "F"], ["S", "B", "D", "C", "F"]]
    flow = {k: 0 for k in FLOW_CAP}
    frames = []

    def snap(path=None):
        g = ge.reset_colors(src)
        vset(g, "S", "#fff9c4", "#f9a825")
        vset(g, "F", "#fff9c4", "#f9a825")
        pe = set(zip(path, path[1:])) if path else set()
        for e in g["edges"]:
            u, w = nm[e["vertex1"]], nm[e["vertex2"]]
            e["weight"] = f"{flow[(u, w)]}/{FLOW_CAP[(u, w)]}"
            if (u, w) in pe:
                e["color"] = e["background"] = P.E_ACTIVE
                e["lineWidth"] = 3.5
            elif flow[(u, w)] > 0:
                e["color"] = e["background"] = GREEN
                e["lineWidth"] = 3.0
            else:
                e["color"] = e["background"] = "#000000"
                e["lineWidth"] = 2.0
        return g

    frames.append(snap())                       # 0: f = 0
    for p in paths:
        d = min(FLOW_CAP[(a, b)] - flow[(a, b)] for a, b in zip(p, p[1:]))
        for a, b in zip(p, p[1:]):
            flow[(a, b)] += d
        frames.append(snap(p))                  # путь подсвечен, f обновлён
    frames.append(snap())                       # итог
    render_series(HERE / "lec09" / "flowexample", "flowex", frames)


# =============================================================================
# ЛЕКЦИЯ 10 — Форд—Фалкерсон (та же сеть)
# =============================================================================
def lec10_ff():
    g = ge.load_graph(FIG / "p23-example-1.graph")
    nm = names_of(g)
    for e in g["edges"]:
        u, w = nm[e["vertex1"]], nm[e["vertex2"]]
        e["weight"] = str(FLOW_CAP[(u, w)])
    out = HERE / "lec10" / "ford_fulkerson"
    out.mkdir(parents=True, exist_ok=True)
    for old in (list(out.glob("ford_fulkerson-*.graph"))
                + list(out.glob("ford_fulkerson-*.pdf"))):
        old.unlink()
    steps = ge.run_ford_fulkerson(g, "S", "F", out, "ford_fulkerson")
    print(f"  lec10/ford_fulkerson: {len(steps)} шагов")
    for s in steps:
        print("    ", s["number"], s["title"], "|", "; ".join(
            a for a in ([] if not s.get("description") else [s["description"]])))
    # вывод аннотаций для подписи в LaTeX
    return steps


def main():
    print("=== make_fixes: генерация фигур и шагов ===")
    lec02_topsort()
    lec03_floyd()
    lec04_bridges()
    lec05_kosaraju()
    lec05_fleury()
    lec05_misc()
    lec06_hamilton()
    lec06_tasks()
    lec07_prim()
    lec08_kruskal()
    lec09_bipartite()
    lec09_matching_small()
    lec09_matching_steps()
    lec09_flow_example()
    lec10_ff()
    print("=== Готово ===")


if __name__ == "__main__":
    main()
