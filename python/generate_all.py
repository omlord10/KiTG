#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_all.py — генерация всех картинок для конспекта КиТГ.

Делает две вещи:
  1) Статические фигуры: рендерит каждый ../figures/*.graph -> ../figures/*.pdf
     (на эти PDF ссылаются \\includegraphics в лекциях).
  2) Пошаговые алгоритмы: обходит подпапки python/*/, в каждой читает
     config.json и <name>-0.graph, запускает алгоритм из graph_engine
     и генерирует <name>-1.graph/.pdf, <name>-2..., и т.д.

Использование:
  python3 generate_all.py            # всё
  python3 generate_all.py --figures  # только статические фигуры
  python3 generate_all.py --steps    # только пошаговые алгоритмы
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any

try:
    import graph_engine as ge
except ModuleNotFoundError as exc:  # cairosvg / networkx не установлены
    missing = getattr(exc, "name", "зависимость")
    sys.stderr.write(
        "\n[generate_all] Не найден модуль: %s\n"
        "Установите зависимости для генерации картинок:\n"
        "  sudo apt install nodejs python3-cairosvg python3-networkx\n"
        "  либо: pip install -r python/requirements.txt --break-system-packages\n\n"
        % missing
    )
    sys.exit(1)

HERE = Path(__file__).parent.resolve()
FIGURES_DIR = HERE.parent / "figures"


# =============================================================================
# 1. Статические фигуры
# =============================================================================

def generate_static_figures() -> int:
    """Рендерит все figures/*.graph -> figures/*.pdf. Возвращает число успехов."""
    if not FIGURES_DIR.exists():
        print(f"  (папка {FIGURES_DIR} не найдена — пропуск статических фигур)")
        return 0

    graph_files = sorted(FIGURES_DIR.glob("*.graph"))
    ok = 0
    for gf in graph_files:
        out = gf.with_suffix(".pdf")
        try:
            graph = ge.load_graph(gf)
            ge.render_graph(graph, out)
            ok += 1
        except Exception as exc:  # noqa: BLE001 — отчёт по каждому файлу
            print(f"  ОШИБКА в {gf.name}: {exc}")
            traceback.print_exc()
    print(f"  Статических фигур отрисовано: {ok}/{len(graph_files)}")
    return ok


# =============================================================================
# 2. Пошаговые алгоритмы
# =============================================================================

def _dispatch(algorithm: str, graph: dict[str, Any], config: dict[str, Any],
              folder: Path, name: str) -> list[dict[str, Any]]:
    """Вызывает нужную функцию алгоритма с параметрами из config.json."""
    fn = ge.ALGORITHMS.get(algorithm)
    if fn is None:
        raise ValueError(f"неизвестный алгоритм '{algorithm}'")

    if algorithm in ("dfs", "bfs", "dijkstra", "bellman_ford", "prim"):
        return fn(graph, config.get("start", graph["vertices"][0]["name"]), folder, name)
    if algorithm in ("kruskal", "topsort"):
        return fn(graph, folder, name)
    if algorithm == "ford_fulkerson":
        return fn(graph, config["source"], config["sink"], folder, name)
    raise ValueError(f"не настроен вызов для '{algorithm}'")


def generate_step_algorithms() -> int:
    """Обходит python/*/ с config.json и генерирует шаги. Возвращает число папок."""
    processed = 0
    subdirs = sorted(p for p in HERE.iterdir() if p.is_dir() and (p / "config.json").exists())
    for folder in subdirs:
        config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        name = config.get("name", folder.name)
        algorithm = config["algorithm"]

        # Входной (авторский) файл — <name>.graph; он НИКОГДА не перезаписывается.
        # Запасной вариант: любой *.graph, не являющийся сгенерированным шагом *-N.graph.
        init_file = folder / f"{name}.graph"
        if not init_file.exists():
            step_re = re.compile(r".*-\d+\.graph$")
            candidates = [g for g in folder.glob("*.graph") if not step_re.match(g.name)]
            if not candidates:
                print(f"  {folder.name}: нет входного файла {name}.graph — пропуск")
                continue
            init_file = candidates[0]

        # Удаляем устаревшие шаги предыдущего запуска (идемпотентность).
        for old in folder.glob(f"{name}-*.graph"):
            old.unlink()
        for old in folder.glob(f"{name}-*.pdf"):
            old.unlink()

        try:
            graph = ge.load_graph(init_file)
            steps = _dispatch(algorithm, graph, config, folder, name)
            print(f"  {folder.name}: {algorithm} -> {len(steps)} шаг(ов)")
            processed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ОШИБКА в {folder.name} ({algorithm}): {exc}")
            traceback.print_exc()
    return processed


# =============================================================================
# main
# =============================================================================

def main() -> None:
    do_figures = "--steps" not in sys.argv
    do_steps = "--figures" not in sys.argv

    print("=== Генерация картинок графов ===")
    if do_figures:
        print("[1] Статические фигуры (figures/*.graph -> *.pdf):")
        generate_static_figures()
    if do_steps:
        print("[2] Пошаговые алгоритмы (python/*/):")
        n = generate_step_algorithms()
        if n == 0:
            print("  (нет настроенных папок — запустите build_demos.py)")
    print("=== Готово ===")


if __name__ == "__main__":
    main()
