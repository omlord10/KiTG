#!/usr/bin/env python3
"""
make_summary.py — Генератор сборников для КиТГ.

Парсит conspec/**/*.tex, извлекает окружения (defn, statement, lemma, algo, task)
и генерирует:
  - summary_defs.tex   (все определения)
  - summary_thms.tex   (все теоремы + леммы)
  - summary_algos.tex  (все алгоритмы)
  - summary_tasks.tex  (все задачи)

Каждый блок в сборнике оборачивается в summary-окружение с номером и ссылкой
на оригинал (через pageref).

Использование:
  python3 make_summary.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# =============================================================================
# Типы окружений и их маппинг на summary-окружения
# =============================================================================

ENV_CONFIG: dict[str, dict[str, str]] = {
    "defn": {
        "summary_env": "summarydefn",
        "counter_prefix": "def",
        "output_file": "summary_defs.tex",
    },
    "statement": {
        "summary_env": "summarythm",
        "counter_prefix": "thm",
        "output_file": "summary_thms.tex",
    },
    "lemma": {
        "summary_env": "summarylemma",
        "counter_prefix": "thm",
        "output_file": "summary_thms.tex",
    },
    "algo": {
        "summary_env": "summaryalgo",
        "counter_prefix": "algo",
        "output_file": "summary_algos.tex",
    },
    "task": {
        "summary_env": "summarytask",
        "counter_prefix": "task",
        "output_file": "summary_tasks.tex",
    },
}

# Порядок окружений, которые делят один счётчик
SHARED_COUNTERS: dict[str, list[str]] = {
    "thm": ["statement", "lemma"],
}


@dataclass
class ExtractedBlock:
    """Один извлечённый блок (определение, теорема, ...)."""
    env_type: str         # defn, statement, lemma, algo, task
    title: str            # Название (первый аргумент)
    key: str              # Ключ/метка (второй аргумент)
    body: str             # Тело окружения
    source_file: str      # Откуда извлечён
    line_number: int      # Номер строки начала
    counter_value: int = 0  # Номер (заполняется при нумерации)
    proof: str = ""        # Доказательство (для statement/lemma), если идёт сразу после


def find_tex_files(base_dir: Path) -> list[Path]:
    """Находит все .tex файлы в conspec/ поддиректориях, отсортированные."""
    conspec_dir = base_dir / "conspec"
    if not conspec_dir.exists():
        print(f"ПРЕДУПРЕЖДЕНИЕ: Папка {conspec_dir} не найдена.", file=sys.stderr)
        return []

    files: list[Path] = []
    for subdir in sorted(conspec_dir.iterdir()):
        if subdir.is_dir() and subdir.name.startswith("conspec"):
            for tex_file in sorted(subdir.glob("*.tex")):
                files.append(tex_file)

    return files


def extract_blocks(tex_file: Path) -> list[ExtractedBlock]:
    """Извлекает все боксы из .tex файла."""
    content = tex_file.read_text(encoding="utf-8")
    blocks: list[ExtractedBlock] = []

    # Паттерн: \begin{env}{title}{key} ... \end{env}
    # Поддерживает многострочный body; ленивый матч до \end{env}
    for env_name in ENV_CONFIG:
        pattern = (
            r"\\begin\{" + re.escape(env_name) + r"\}"
            r"\s*\{([^}]*)\}"    # {title}
            r"\s*\{([^}]*)\}"    # {key}
            r"(.*?)"             # body (ленивый)
            r"\\end\{" + re.escape(env_name) + r"\}"
        )
        for match in re.finditer(pattern, content, re.DOTALL):
            title = match.group(1).strip()
            key = match.group(2).strip()
            body = match.group(3).strip()

            # Вычисляем номер строки
            line_number = content[:match.start()].count("\n") + 1

            # Для теорем и лемм пытаемся захватить доказательство,
            # идущее сразу после \end{env} (допускаем пробелы/комментарии).
            proof = ""
            if env_name in ("statement", "lemma"):
                tail = content[match.end():]
                m_pr = re.match(
                    r"\s*(?:%[^\n]*\n\s*)*\\begin\{proof\}"
                    r"(?:\[[^\]]*\])?"      # опциональный заголовок [Доказательство ...]
                    r"(.*?)\\end\{proof\}",
                    tail, re.DOTALL)
                if m_pr:
                    proof = m_pr.group(1).strip()

            blocks.append(ExtractedBlock(
                env_type=env_name,
                title=title,
                key=key,
                body=body,
                source_file=str(tex_file),
                line_number=line_number,
                proof=proof,
            ))

    return blocks


def assign_counter_values(blocks: list[ExtractedBlock]) -> None:
    """Присваивает сквозные номера каждому блоку (как в итоговом PDF)."""
    counters: dict[str, int] = {}

    for block in blocks:
        prefix = ENV_CONFIG[block.env_type]["counter_prefix"]
        counters.setdefault(prefix, 0)
        counters[prefix] += 1
        block.counter_value = counters[prefix]


def load_defs_examples(base_dir: Path) -> dict[str, str]:
    """Подгружает дополнительные примеры для определений (defs_examples.py)."""
    examples_file = base_dir / "defs_examples.py"
    if not examples_file.exists():
        return {}
    namespace: dict = {}
    exec(examples_file.read_text(encoding="utf-8"), namespace)
    return namespace.get("EXAMPLES", {})


DEFS_EXAMPLES: dict[str, str] = {}


def render_block(block: ExtractedBlock) -> str:
    """Рендерит один блок в summary-окружение (с номером и ссылкой)."""
    config = ENV_CONFIG[block.env_type]
    summary_env = config["summary_env"]
    prefix = config["counter_prefix"]
    label = f"{prefix}:{block.key}"
    body = block.body
    if block.env_type in ("statement", "lemma") and block.proof:
        body += ("\n\n\\par\\medskip\\noindent"
                 "\\rule{\\linewidth}{0.4pt}\\par\\smallskip\n"
                 "\\noindent\\textbf{Доказательство.} "
                 + block.proof + " $\\blacksquare$")
    if block.env_type == "defn" and block.key in DEFS_EXAMPLES:
        body += ("\n\n\\par\\medskip\\noindent"
                 "\\rule{\\linewidth}{0.4pt}\\par\\smallskip\n"
                 "\\noindent\\textbf{Примеры (дополнительные).}\n"
                 + DEFS_EXAMPLES[block.key].strip())
    return (
        f"\\begin{{{summary_env}}}{{{block.counter_value}}}{{{block.title}}}{{{label}}}\n"
        f"{body}\n"
        f"\\end{{{summary_env}}}\n"
    )


def main() -> None:
    base_dir = Path(__file__).parent.resolve()
    global DEFS_EXAMPLES
    DEFS_EXAMPLES = load_defs_examples(base_dir)
    if DEFS_EXAMPLES:
        print(f"Примеров к определениям: {len(DEFS_EXAMPLES)}")
    tex_files = find_tex_files(base_dir)

    if not tex_files:
        print("Файлы .tex не найдены в conspec/. Генерирую пустые сборники.")

    # Собираем все блоки в порядке появления в файлах
    all_blocks: list[ExtractedBlock] = []
    for tf in tex_files:
        file_blocks = extract_blocks(tf)
        file_blocks.sort(key=lambda b: b.line_number)
        all_blocks.extend(file_blocks)
        if file_blocks:
            print(f"  {tf.name}: {len(file_blocks)} блок(ов)")

    # Присваиваем сквозные номера (в порядке документа)
    assign_counter_values(all_blocks)
    print(f"\nВсего извлечено блоков: {len(all_blocks)}")

    # Группируем блоки по выходным файлам, СОХРАНЯЯ порядок документа
    # (важно для summary_thms.tex: теоремы и леммы делят счётчик и должны
    #  идти вперемежку по возрастанию номера).
    output_order = ["summary_defs.tex", "summary_thms.tex",
                    "summary_algos.tex", "summary_tasks.tex"]
    grouped: dict[str, list[ExtractedBlock]] = {f: [] for f in output_order}
    for block in all_blocks:
        grouped[ENV_CONFIG[block.env_type]["output_file"]].append(block)

    for filename in output_order:
        blocks = grouped[filename]
        header = [
            "% Автоматически сгенерировано make_summary.py",
            f"% Элементов: {len(blocks)}",
            "",
        ]
        body = [render_block(b) for b in blocks] if blocks else ["% (пусто)\n"]
        out_path = base_dir / filename
        out_path.write_text("\n".join(header) + "\n".join(body), encoding="utf-8")
        print(f"  Записан: {filename} ({len(blocks)} блок(ов))")

    print("\nГотово!")


if __name__ == "__main__":
    main()
