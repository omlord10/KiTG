#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_steps.py — пошаговая визуализация алгоритмов на РЕАЛЬНЫХ графах лекций.

В отличие от прежнего build_demos.py (где все графы имели одинаковую структуру
S,A,B,C,D,F), здесь для каждого алгоритма берётся СВОЙ граф из figures/ (по
таблице STEP_MAP), при необходимости детерминированно проставляются веса/
пропускные способности, после чего алгоритм прокручивается по шагам, а кадры
раскладываются по ПО-ЛЕКЦИОННЫМ папкам python/lecNN/<algo>/ и рендерятся
движком programforyou (через graph_engine -> pfy_render).

Запуск:  python3 python/generate_steps.py
"""
from __future__ import annotations

import json
from pathlib import Path

import graph_engine as ge

HERE = Path(__file__).parent
FIG = HERE.parent / "figures"

# (лекция, алгоритм, исходный_граф, параметры)
#   weights=(lo,hi)  — проставить веса рёбрам, если их нет
#   caps=(lo,hi)     — проставить пропускные способности (для потока)
#   start            — стартовая вершина (по умолчанию — первая)
#   source/sink      — для потока
STEP_MAP = [
    ("02", "dfs",            "dfs-example.graph",          {}),
    ("02", "bfs",            "bfs-example.graph",          {}),
    ("07", "prim",           "p19-prim-example-1.graph",   {"weights": (1, 9), "start": "A"}),
    ("08", "kruskal",        "p20-kraskal-example-1.graph", {"weights": (1, 9)}),
    ("13", "dijkstra",       "p9-example-0.graph",         {"weights": (1, 9), "start": "A"}),
    ("13", "bellman_ford",   "p30-fb-example-1.graph",     {"start": "A"}),
    ("10", "ford_fulkerson", "p23-example-1.graph",        {"caps": (4, 12), "source": "S", "sink": "F"}),
    ("02", "topsort",        "dag-example.graph",          {}),
    ("05", "kosaraju",       "p12-example-1.graph",        {}),
    ("04", "bridges",        "p11-example-2.graph",        {}),
    ("09", "matching",       "match-example.graph",        {}),
    ("06", "pruefer",        "p17-pruffer-example-1.graph", {}),
]


def _assign_weights(graph: dict, lo: int, hi: int) -> None:
    """Детерминированно проставляет веса рёбрам (стабильно и по-разному для
    разных графов — зависит от имён концов и индекса ребра)."""
    span = hi - lo + 1
    nbi = {i: v["name"] for i, v in enumerate(graph["vertices"])}
    for idx, e in enumerate(graph["edges"]):
        u, w = nbi[e["vertex1"]], nbi[e["vertex2"]]
        h = sum(ord(c) for c in (u + w)) + 3 * idx
        e["weight"] = str(lo + (h % span))


def _start_vertex(graph: dict, params: dict) -> str:
    if "start" in params:
        return params["start"]
    return graph["vertices"][0]["name"]


def main() -> int:
    total = 0
    for lecture, algo, src, params in STEP_MAP:
        src_path = FIG / src
        if not src_path.exists():
            print(f"  [{lecture}/{algo}] нет графа {src} — пропуск")
            continue
        graph = ge.load_graph(src_path)

        if "weights" in params and not any(
            str(e.get("weight", "")).strip() for e in graph["edges"]
        ):
            _assign_weights(graph, *params["weights"])
        if "caps" in params:
            _assign_weights(graph, *params["caps"])

        out_dir = HERE / f"lec{lecture}" / algo
        out_dir.mkdir(parents=True, exist_ok=True)
        name = algo

        if algo in ("dfs", "bfs", "dijkstra", "bellman_ford", "prim"):
            fn = getattr(ge, f"run_{algo}")
            steps = fn(graph, _start_vertex(graph, params), out_dir, name)
        elif algo == "kruskal":
            steps = ge.run_kruskal(graph, out_dir, name)
        elif algo in ("topsort", "kosaraju", "bridges", "matching", "pruefer"):
            steps = getattr(ge, f"run_{algo}")(graph, out_dir, name)
        elif algo == "ford_fulkerson":
            steps = ge.run_ford_fulkerson(
                graph, params["source"], params["sink"], out_dir, name
            )
        else:
            print(f"  [{lecture}/{algo}] неизвестный алгоритм — пропуск")
            continue

        print(f"  lec{lecture}/{algo}: {src} -> {len(steps)} шаг(ов)")
        total += 1
    print(f"=== Готово: {total} серий шагов ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
