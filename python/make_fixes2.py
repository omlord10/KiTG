#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_fixes2.py — фигуры для лекций 11–14.

  * лек. 11 — push-relabel: сеть с σ, 14 кадров (h/ε у вершин);
              раскрашенные K4 (χ=4) и C5 (χ=3);
  * лек. 12 — раскраска P4/дерева (иллюстрация t(t-1)^{n-1});
              иллюстрация теоремы о редукции (3 мини-графа);
  * лек. 13 — починка весов A→D=2 в p29-djakstra-example-1 и
              p31-fu-example-1;
  * лек. 14 — починка p32-f-example-1 / p33-jonson-example-1 под текст
              лекции; кадры Флойда (ведущая вершина + ярлыки);
              граф задачи (task-floyd-1); перевешенный граф Джонсона.
"""
from __future__ import annotations

import collections
from pathlib import Path

import graph_engine as ge
from make_fixes import (V, E, T, G, names_of, idx_of, vset, eset, eall,
                        save_render, render_series,
                        BLUE_BG, BLUE_BD, ORNG_BG, ORNG_BD,
                        RED, GREEN, LIGHT, GRAY)

HERE = Path(__file__).parent
FIG = HERE.parent / "figures"

YELL_BG, YELL_BD = "#fff9c4", "#f9a825"


# =============================================================================
# ЛЕКЦИЯ 11 — push-relabel
# =============================================================================
PR_CAP = {("S", "A"): 3, ("S", "B"): 2, ("A", "C"): 3, ("A", "B"): 1,
          ("B", "D"): 3, ("D", "C"): 2, ("C", "F"): 2, ("D", "F"): 3}

# координаты как в p23-example-1 (S слева, F справа)
PR_POS = {"S": (60, 220), "A": (240, 100), "B": (240, 340),
          "C": (470, 100), "D": (470, 340), "F": (650, 220)}


def _pr_graph(flow, h, ex, hl_vertex=None, push_edge=None, lifted=None):
    verts = []
    names = list(PR_POS)
    for n in names:
        x, y = PR_POS[n]
        v = V(n, x, y)
        if n in ("S", "F"):
            v["background"], v["border"] = YELL_BG, YELL_BD
        if n == hl_vertex:
            v["background"], v["border"] = ORNG_BG, ORNG_BD
        if n == lifted:
            v["background"], v["border"] = BLUE_BG, BLUE_BD
        verts.append(v)
    ix = {n: i for i, n in enumerate(names)}
    edges = []
    for (u, w), c in PR_CAP.items():
        e = E(ix[u], ix[w], f"{flow[(u, w)]}/{c}", directed=True)
        if push_edge == (u, w) or push_edge == (w, u):
            e["color"] = e["background"] = "#e65100"
            e["lineWidth"] = 3.5
        elif flow[(u, w)] > 0:
            e["color"] = e["background"] = GREEN
            e["lineWidth"] = 3.0
        edges.append(e)
    texts = []
    for n in names:
        x, y = PR_POS[n]
        lbl = f"h={h[n]}, ε={ex[n]}"
        texts.append(T(x, y + 42, lbl, width=120, bg="#f3e5f5",
                       bd="#7b1fa2"))
    return G(verts, edges, texts)


def lec11_push_relabel():
    # сеть-условие (только пропускные способности)
    g0 = _pr_graph({k: 0 for k in PR_CAP},
                   {n: 0 for n in PR_POS}, {n: 0 for n in PR_POS})
    for e in g0["edges"]:
        nm = names_of(g0)
        u, w = nm[e["vertex1"]], nm[e["vertex2"]]
        e["weight"] = str(PR_CAP[(u, w)])
    g0["texts"] = []
    save_render(g0, FIG / "p25-example-1.graph")

    # симуляция
    Vs = list(PR_POS)
    NEIGH = ["C", "D", "F", "B", "A", "S"]
    res = collections.defaultdict(int)
    for (u, w), c in PR_CAP.items():
        res[(u, w)] = c
    h = {n: 0 for n in Vs}
    h["S"] = len(Vs)
    ex = {n: 0 for n in Vs}
    flow = collections.defaultdict(int)
    for (u, w), c in PR_CAP.items():
        if u == "S":
            res[(u, w)] = 0
            res[(w, u)] += c
            ex[w] += c
            ex["S"] -= c
            flow[(u, w)] = c
    frames = [_pr_graph(flow, h, ex)]

    def active():
        for n in ["A", "B", "C", "D"]:
            if ex[n] > 0:
                return n

    while True:
        v = active()
        if v is None:
            break
        pushed = False
        for u in NEIGH:
            if res[(v, u)] > 0 and h[v] == h[u] + 1:
                d = min(ex[v], res[(v, u)])
                res[(v, u)] -= d
                res[(u, v)] += d
                ex[v] -= d
                ex[u] += d
                if (v, u) in PR_CAP:
                    flow[(v, u)] += d
                elif (u, v) in PR_CAP:
                    flow[(u, v)] -= d
                frames.append(_pr_graph(flow, h, ex, hl_vertex=v,
                                        push_edge=(v, u)))
                pushed = True
                break
        if not pushed:
            h[v] = 1 + min(h[u] for u in Vs if res[(v, u)] > 0)
            frames.append(_pr_graph(flow, h, ex, lifted=v))
    render_series(HERE / "lec11" / "push_relabel", "pr", frames)
    print("   |f| =", ex["F"], " flow:", dict(flow))


def lec11_chromatic():
    cols = [("#ffcdd2", "#c62828"), ("#bbdefb", "#1565c0"),
            ("#c8e6c9", "#2e7d32"), ("#fff9c4", "#f9a825")]
    # K4 — 4 цвета
    g = ge.load_graph(FIG / "p25-example-2.graph")
    g = ge.reset_colors(g)
    eall(g, "#000000", 2.0)
    for i, n in enumerate(names_of(g)):
        bg, bd = cols[i % 4]
        vset(g, n, bg, bd)
    save_render(g, FIG / "p25-example-2.graph")
    # C5 — 3 цвета: 1,2,1,2,3
    g = ge.load_graph(FIG / "p25-example-3.graph")
    g = ge.reset_colors(g)
    eall(g, "#000000", 2.0)
    assign = {"1": 0, "2": 1, "3": 0, "4": 1, "5": 2}
    for n, ci in assign.items():
        bg, bd = cols[ci]
        vset(g, n, bg, bd)
    save_render(g, FIG / "p25-example-3.graph")


# =============================================================================
# ЛЕКЦИЯ 12 — хроматический многочлен
# =============================================================================
def lec12_examples():
    cols = [("#ffcdd2", "#c62828"), ("#bbdefb", "#1565c0"),
            ("#c8e6c9", "#2e7d32")]
    # P4: пример правильной раскраски в 2 цвета (1,2,1,2)
    g = ge.load_graph(FIG / "p26-example-1.graph")
    g = ge.reset_colors(g)
    eall(g, "#000000", 2.0)
    for n, ci in {"1": 0, "2": 1, "3": 0, "4": 1}.items():
        bg, bd = cols[ci]
        vset(g, n, bg, bd)
    save_render(g, FIG / "p26-example-1.graph")
    # дерево-звезда 2-(1,3,4): корень 2 цветом 1, листья цветом 2
    g = ge.load_graph(FIG / "p26-example-2.graph")
    g = ge.reset_colors(g)
    eall(g, "#000000", 2.0)
    for n, ci in {"1": 1, "2": 0, "3": 1, "4": 1}.items():
        bg, bd = cols[ci]
        vset(g, n, bg, bd)
    save_render(g, FIG / "p26-example-2.graph")

    # Иллюстрация теоремы о редукции: G (путь u-w-v), G∨uv, G*uv
    def base(extra_edge=False):
        vs = [V("u", 80, 220), V("w", 230, 90), V("v", 380, 220)]
        es = [E(0, 1), E(1, 2)]
        if extra_edge:
            es.append(E(0, 2, color=GREEN, background=GREEN, lineWidth=3.0))
        return G(vs, es)

    save_render(base(False), FIG / "p26-red-0.graph")
    save_render(base(True), FIG / "p26-red-1.graph")
    merged = G([V("uv", 150, 220, background="#e1bee7", border="#7b1fa2"),
                V("w", 300, 90)],
               [E(0, 1)])
    save_render(merged, FIG / "p26-red-2.graph")


# =============================================================================
# ЛЕКЦИЯ 13 — починка весов A→D
# =============================================================================
def lec13_fix_weights():
    for fname in ["p29-djakstra-example-1.graph", "p31-fu-example-1.graph"]:
        g = ge.load_graph(FIG / fname)
        nm = names_of(g)
        for e in g["edges"]:
            u, w = nm[e["vertex1"]], nm[e["vertex2"]]
            if (u, w) == ("A", "D"):
                e["weight"] = "2"
        save_render(g, FIG / fname)
        print(f"  {fname}: A→D := 2")


# =============================================================================
# ЛЕКЦИЯ 14 — Флойд и Джонсон
# =============================================================================
F_POS = {"A": (110, 90), "B": (380, 90), "C": (380, 330), "D": (110, 330)}
F_EDGES = [("A", "B", 1), ("B", "C", 1), ("B", "D", 3),
           ("C", "A", -2), ("C", "D", 1), ("D", "A", 4)]


def _floyd_graph(extra=None, lead=None):
    """extra: список (u, w, label, color) добавленных «ярлыков»."""
    names = list(F_POS)
    vs = []
    for n in names:
        x, y = F_POS[n]
        v = V(n, x, y)
        if n == lead:
            v["background"], v["border"] = ORNG_BG, ORNG_BD
        vs.append(v)
    ix = {n: i for i, n in enumerate(names)}
    es = []
    for u, w, wt in F_EDGES:
        e = E(ix[u], ix[w], wt, directed=True)
        if (u, w) == ("B", "D"):
            e["controlStep"] = -45
        elif (u, w) == ("C", "A"):
            e["controlStep"] = 45
        es.append(e)
    for (u, w, lbl, colr, bend) in (extra or []):
        e = E(ix[u], ix[w], lbl, directed=True,
              color=colr, background=colr, lineWidth=2.4)
        e["controlStep"] = bend
        es.append(e)
    return G(vs, es)


def lec14_floyd():
    # корректный рисунок-условие
    save_render(_floyd_graph(), FIG / "p32-f-example-1.graph")

    frames = [_floyd_graph()]
    added = []          # накопленные «ярлыки» (без весов, светлые)
    new_per_step = {
        "A": [("C", "B", "-1"), ("D", "B", "5")],
        "B": [("A", "C", "2"), ("A", "D", "4"), ("D", "C", "6")],
        "C": [("A", "D", "3"), ("B", "A", "-1"), ("B", "D", "2")],
        "D": [],
    }
    bend = {("C", "B"): 60, ("D", "B"): 60, ("A", "C"): 60,
            ("A", "D"): -60, ("D", "C"): 100, ("B", "A"): 60,
            ("B", "D"): 100}
    for lead in ["A", "B", "C", "D"]:
        cur = []
        seen = set()
        news = new_per_step[lead]
        new_keys = {(u, w) for u, w, _ in news}
        # старые ярлыки (light), перекрытые новыми — убираем
        for (u, w, lbl) in added:
            if (u, w) not in new_keys and (u, w) not in seen:
                cur.append((u, w, "", LIGHT, bend[(u, w)]))
                seen.add((u, w))
        for (u, w, lbl) in news:
            cur.append((u, w, lbl, GREEN, bend[(u, w)]))
        frames.append(_floyd_graph(cur, lead=lead))
        # обновляем накопитель
        added = [(u, w, l) for (u, w, l) in added if (u, w) not in new_keys]
        added += news
    render_series(HERE / "lec14" / "floyd", "floyd", frames)

    # граф задачи 10 (Флойд): AB3, AC8, BC2, BD5, CD1, DA2
    pos = {"A": (110, 90), "B": (380, 90), "C": (380, 330), "D": (110, 330)}
    names = list(pos)
    vs = [V(n, *pos[n]) for n in names]
    ix = {n: i for i, n in enumerate(names)}
    es = [E(ix["A"], ix["B"], 3, directed=True),
          E(ix["A"], ix["C"], 8, directed=True),
          E(ix["B"], ix["C"], 2, directed=True),
          E(ix["B"], ix["D"], 5, directed=True),
          E(ix["C"], ix["D"], 1, directed=True),
          E(ix["D"], ix["A"], 2, directed=True)]
    save_render(G(vs, es), FIG / "task-floyd-1.graph")


def lec14_johnson():
    # граф + фиктивная S (корректные направления)
    pos = dict(F_POS)
    pos["S"] = (-20, 210)
    names = list(pos)
    vs = []
    for n in names:
        x, y = pos[n]
        v = V(n, x, y)
        if n == "S":
            v["background"], v["border"] = YELL_BG, YELL_BD
        vs.append(v)
    ix = {n: i for i, n in enumerate(names)}
    es = []
    for u, w, wt in F_EDGES:
        e = E(ix[u], ix[w], wt, directed=True)
        if (u, w) in (("B", "D"), ("C", "A")):
            e["controlStep"] = -90
        es.append(e)
    for t in ["A", "B", "C", "D"]:
        es.append(E(ix["S"], ix[t], 0, directed=True,
                    color=BLUE_BD, background=BLUE_BD))
    save_render(G(vs, es), FIG / "p33-jonson-example-1.graph")

    # перевешенный граф (σ̃)
    new_w = {("A", "B"): 0, ("B", "C"): 0, ("B", "D"): 2,
             ("C", "A"): 0, ("C", "D"): 1, ("D", "A"): 6}
    names = list(F_POS)
    vs = [V(n, *F_POS[n]) for n in names]
    ix = {n: i for i, n in enumerate(names)}
    es = [E(ix[u], ix[w], new_w[(u, w)], directed=True)
          for u, w, _ in F_EDGES]
    save_render(G(vs, es), FIG / "p33-jonson-2.graph")


def main():
    print("=== make_fixes2: лекции 11–14 ===")
    lec11_push_relabel()
    lec11_chromatic()
    lec12_examples()
    lec13_fix_weights()
    lec14_floyd()
    lec14_johnson()
    print("=== готово ===")


if __name__ == "__main__":
    main()
