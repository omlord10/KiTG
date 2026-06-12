#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pfy_render.py — рендер .graph -> PDF через ОФЛАЙН-движок programforyou.

Движок редактора графов programforyou.ru целиком встроен в HTML; мы извлекли
его (python/pfy/engine.js) и запускаем в Node с минимальными шимами браузерных
API (python/pfy/shim.js + harness.js). На выходе — векторный SVG, идентичный
тому, что отдаёт сайт по кнопке «Скачать .svg». SVG конвертируется в PDF через
cairosvg. Сеть и браузер не нужны.

Требования: node (>=16), python-пакет cairosvg.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import cairosvg

PFY_DIR = Path(__file__).parent / "pfy"
_BUNDLE = PFY_DIR / "_bundle.js"


def _ensure_bundle() -> Path:
    """Собирает (при необходимости) единый bundle shim+engine+harness."""
    parts = [PFY_DIR / "shim.js", PFY_DIR / "engine.js", PFY_DIR / "harness.js"]
    newest = max(p.stat().st_mtime for p in parts)
    if not _BUNDLE.exists() or _BUNDLE.stat().st_mtime < newest:
        with _BUNDLE.open("w", encoding="utf-8") as out:
            for p in parts:
                out.write(p.read_text(encoding="utf-8"))
                out.write("\n;\n")
    return _BUNDLE


def render_to_svg(graph_path: str | Path, svg_path: str | Path) -> None:
    """Рендерит .graph -> .svg движком programforyou (через Node)."""
    bundle = _ensure_bundle()
    res = subprocess.run(
        ["node", str(bundle), str(graph_path), str(svg_path)],
        capture_output=True, text=True,
    )
    if res.returncode != 0 or not Path(svg_path).exists():
        raise RuntimeError(
            f"pfy render failed for {graph_path}:\n{res.stderr.strip()}"
        )


def render_to_pdf(graph_path: str | Path, pdf_path: str | Path,
                  width: int = 600) -> None:
    """Рендерит .graph -> .pdf (programforyou SVG -> cairosvg)."""
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        svg_tmp = Path(tmp.name)
    try:
        render_to_svg(graph_path, svg_tmp)
        cairosvg.svg2pdf(url=str(svg_tmp), write_to=str(pdf_path),
                         output_width=width)
    finally:
        svg_tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: pfy_render.py in.graph out.pdf")
        sys.exit(1)
    render_to_pdf(sys.argv[1], sys.argv[2])
    print("OK", sys.argv[2])
