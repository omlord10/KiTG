#!/bin/bash
# =============================================================================
# build.sh — КиТГ: полная сборка проекта
#
# Использование:
#   ./build.sh          — полная сборка (картинки + сборники + PDF)
#   ./build.sh --quick  — только LaTeX (без Python-генерации картинок)
#
# Зависимости Python (для генерации картинок): matplotlib, networkx.
#   Kubuntu/Debian:  sudo apt install nodejs python3-cairosvg python3-networkx
#   либо:            pip install -r python/requirements.txt --break-system-packages   (нужен также Node.js: sudo apt install nodejs)
# =============================================================================
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

QUICK=0
if [ "$1" = "--quick" ]; then
    QUICK=1
fi

echo "╔══════════════════════════════════════════════╗"
echo "║  КиТГ — Сборка конспекта                    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# --- [1/4] Генерация картинок графов ---
# Запускаем БЕЗ смены текущей папки: generate_all.py сам находит пути
# относительно своего расположения (Path(__file__)). Ошибка генерации
# НЕ прерывает сборку — конспект всё равно соберётся (без свежих картинок).
if [ "$QUICK" -eq 0 ] && [ -f python/generate_all.py ]; then
    echo "=== [1/4] Генерация картинок графов ==="
    if python3 python/generate_all.py && python3 python/generate_steps.py; then
        echo "  картинки — готовы"
    else
        echo ""
        echo "  !! Не удалось сгенерировать картинки."
        echo "  !! Скорее всего не установлены matplotlib / networkx."
        echo "  !! Установите:  sudo apt install nodejs python3-cairosvg python3-networkx"
        echo "  !!         или: pip install -r python/requirements.txt --break-system-packages   (нужен также Node.js: sudo apt install nodejs)"
        echo "  !! Сборка продолжится с уже имеющимися PDF (если они есть)."
    fi
    echo ""
else
    echo "=== [1/4] Пропуск генерации картинок (--quick или нет скрипта) ==="
    echo ""
fi

# --- [2/4] Генерация сборников ---
echo "=== [2/4] Генерация сборников ==="
python3 "$ROOT/make_summary.py"
echo ""

# --- [3/4] Компиляция main.pdf ---
echo "=== [3/4] Компиляция main.pdf (3 прохода) ==="
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
echo "  main.pdf — готов"
echo ""

# --- [4/4] Компиляция stand-alone PDF ---
echo "=== [4/4] Компиляция stand-alone PDF ==="
for f in standalone_defs standalone_thms standalone_algos; do
    if [ -f "${f}.tex" ]; then
        pdflatex -interaction=nonstopmode "${f}.tex" > /dev/null 2>&1 || true
        pdflatex -interaction=nonstopmode "${f}.tex" > /dev/null 2>&1 || true
        echo "  ${f}.pdf — готов"
    fi
done
echo ""

# --- Очистка ---
echo "=== Очистка вспомогательных файлов ==="
rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk
rm -f standalone_*.aux standalone_*.log standalone_*.out
echo "  Очищено"
echo ""

# --- Результат ---
echo "╔══════════════════════════════════════════════╗"
echo "║  Готово!                                     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
ls -lh main.pdf standalone_*.pdf 2>/dev/null || echo "(stand-alone PDF ещё не созданы)"
