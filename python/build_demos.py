#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_demos.py — создаёт демонстрационные папки алгоритмов в python/.

Каждая папка содержит <name>-0.graph (шаг инициализации) и config.json
(алгоритм + параметры). generate_all.py использует их как вход.
Запускается один раз при подготовке проекта.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

VSTYLE = dict(radius=20, background="#ffffff", fontSize=18,
              color="#000000", border="#000000")
ESTYLE = dict(controlStep=0, fontSize=18, lineWidth=2,
              background="#000000", color="#000000")


def V(name, x, y):
    return {"x": x, "y": y, "name": name, **VSTYLE}


def E(i, j, w="", directed=False):
    return {"vertex1": i, "vertex2": j, "weight": str(w),
            "isDirected": directed, **ESTYLE}


# Базовая раскладка S,A,B,C,D,F (x — вправо, y — вниз, как в graph.online).
POS = {
    "S": (100, 300), "A": (300, 150), "B": (300, 450),
    "C": (550, 150), "D": (550, 450), "F": (750, 300),
}
NAMES = ["S", "A", "B", "C", "D", "F"]
IDX = {n: i for i, n in enumerate(NAMES)}


def make_vertices():
    return [V(n, *POS[n]) for n in NAMES]


def graph(edges):
    return {"x0": 0, "y0": 0, "vertices": make_vertices(),
            "edges": edges, "texts": []}


def write(folder, gdict, config):
    d = HERE / folder
    d.mkdir(exist_ok=True)
    name = config["name"]
    with (d / f"{name}.graph").open("w", encoding="utf-8") as fh:
        json.dump(gdict, fh, ensure_ascii=False, indent=2)
    with (d / "config.json").open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
    print(f"  {folder}/{name}.graph + config.json")


def e(u, v, w="", d=False):
    return E(IDX[u], IDX[v], w, d)


# --- Неориентированный невзвешенный граф (DFS / BFS) ---
und_simple = [e("S", "A"), e("S", "B"), e("A", "C"), e("A", "B"),
              e("B", "D"), e("C", "D"), e("C", "F"), e("D", "F")]

# --- Неориентированный взвешенный (Дейкстра / Прим / Краскал) ---
und_weighted = [e("S", "A", 2), e("S", "B", 5), e("A", "B", 1),
                e("A", "C", 4), e("B", "D", 3), e("C", "D", 1),
                e("C", "F", 6), e("D", "F", 2)]

# --- Ориентированный взвешенный с отрицательным ребром (Форд—Беллман) ---
dir_negative = [e("S", "A", 3, True), e("S", "B", 2, True), e("A", "C", 2, True),
                e("B", "A", -2, True), e("C", "D", 1, True), e("B", "D", 5, True),
                e("D", "F", 3, True), e("C", "F", 6, True)]

# --- DAG (топологическая сортировка) ---
dag = [e("S", "A", "", True), e("S", "B", "", True), e("A", "C", "", True),
       e("A", "D", "", True), e("B", "D", "", True), e("C", "F", "", True),
       e("D", "F", "", True)]

# --- Сеть для Форда—Фалкерсона (макс. поток = 5, мин. разрез = {C→F, D→F}) ---
network = [e("S", "A", 3, True), e("S", "B", 2, True), e("A", "C", 3, True),
           e("B", "D", 2, True), e("C", "D", 1, True), e("C", "F", 2, True),
           e("D", "F", 3, True)]


def main():
    print("Создаю демо-папки алгоритмов:")
    write("01-dfs", graph(und_simple), {"algorithm": "dfs", "start": "S", "name": "1-dfs"})
    write("02-bfs", graph(und_simple), {"algorithm": "bfs", "start": "S", "name": "2-bfs"})
    write("03-dijkstra", graph(und_weighted),
          {"algorithm": "dijkstra", "start": "S", "name": "3-dijkstra"})
    write("04-bellman-ford", graph(dir_negative),
          {"algorithm": "bellman_ford", "start": "S", "name": "4-bellman-ford"})
    write("05-prim", graph(und_weighted),
          {"algorithm": "prim", "start": "S", "name": "5-prim"})
    write("06-kruskal", graph(und_weighted),
          {"algorithm": "kruskal", "name": "6-kruskal"})
    write("07-topsort", graph(dag), {"algorithm": "topsort", "name": "7-topsort"})
    write("10-ford-fulkerson", graph(network),
          {"algorithm": "ford_fulkerson", "source": "S", "sink": "F",
           "name": "10-ford-fulkerson"})
    print("Готово.")


if __name__ == "__main__":
    main()
