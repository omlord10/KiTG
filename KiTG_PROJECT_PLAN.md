# Проект: LaTeX-конспект по КиТГ (Комбинаторика и Теория Графов)

## Общая архитектура проекта

```
KiTG/
├── build.sh                    # Главный билдер
├── main.tex                    # Основной документ
├── template.tex                # Шаблон (пакеты, стили, окружения)
├── titlepage.tex               # Титульная страница
├── make_summary.py             # Генератор сборников (определения, теоремы, алгоритмы, задачи)
├── summary_defs.tex            # [АВТОГЕН] Все определения
├── summary_thms.tex            # [АВТОГЕН] Все теоремы
├── summary_algos.tex           # [АВТОГЕН] Все алгоритмы
├── summary_tasks.tex           # [АВТОГЕН] Все задачи
├── standalone_defs.tex         # [АВТОГЕН] Stand-alone PDF определений
├── standalone_thms.tex         # [АВТОГЕН] Stand-alone PDF теорем
├── standalone_algos.tex        # [АВТОГЕН] Stand-alone PDF алгоритмов
├── conspec/                    # Контент лекций
│   ├── conspec01/
│   │   ├── conspec01_page1.tex
│   │   ├── conspec01_page2.tex
│   │   └── ...
│   ├── conspec02/
│   └── ...  (до ~14)
├── python/                     # Генератор картинок графов
│   ├── graph_engine.py         # Движок: чтение .graph, алгоритмы, рендер
│   ├── generate_all.py         # Главный скрипт: обходит все папки, генерит PDF
│   ├── 1-dfs/
│   │   ├── 1-dfs-0.graph       # Исходный граф (шаг 0 — инициализация)
│   │   ├── 1-dfs-1.graph       # [АВТОГЕН] Шаг 1
│   │   ├── 1-dfs-2.graph       # [АВТОГЕН] Шаг 2
│   │   ├── 1-dfs-0.pdf         # [АВТОГЕН] Картинка шага 0
│   │   ├── 1-dfs-1.pdf         # [АВТОГЕН] Картинка шага 1
│   │   └── ...
│   ├── 2-bfs/
│   └── ...
└── figures/                    # Прочие картинки (не алгоритмы)
```

---

## Система нумерации

Четыре **независимых сквозных** счётчика (не привязаны к главам, не сбрасываются):

| Счётчик       | Префикс метки | Пример            |
|---------------|---------------|--------------------|
| `defncounter` | `def:`        | Определение 1, 2, 3... |
| `thmcounter`  | `thm:`        | Теорема 1, 2, 3...     |
| `algocounter` | `algo:`       | Алгоритм 1, 2, 3...    |
| `taskcounter` | `task:`       | Задача 1, 2, 3...      |

Каждый счётчик идёт с 1 до N **сквозь весь документ**. Они не пересекаются: Определение 3 и Алгоритм 3 — разные вещи.

---

## Фишки итогового PDF

- Оглавление с гиперссылками
- Красивые tcolorbox: определения (синие), теоремы/леммы (фиолетовые), алгоритмы (зелёные), задачи (оранжевые), доказательства (серые)
- В конце main.pdf: «Все определения», «Все теоремы», «Все алгоритмы», «Все задачи» — каждый бокс со ссылкой на оригинал (стр. N)
- Отдельные stand-alone PDF: `definitions.pdf`, `theorems.pdf`, `algorithms.pdf`
- Автогенерация картинок графов (шаги алгоритмов, цветные, с пояснениями)

---

## build.sh — билд-скрипт

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== [1/4] Генерация картинок графов ==="
cd python && python3 generate_all.py && cd ..

echo "=== [2/4] Генерация сборников ==="
python3 make_summary.py

echo "=== [3/4] Компиляция main.pdf ==="
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

echo "=== [4/4] Компиляция stand-alone PDF ==="
pdflatex -interaction=nonstopmode standalone_defs.tex
pdflatex -interaction=nonstopmode standalone_thms.tex
pdflatex -interaction=nonstopmode standalone_algos.tex

echo "=== Очистка ==="
rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk
rm -f *.defs *.thms *.algos *.tasks
rm -f standalone_*.aux standalone_*.log standalone_*.out

echo "=== Готово! ==="
ls -lh main.pdf standalone_*.pdf
```

---

---

# ПРОМПТ 1: Перенос конспекта из PDF-фотографий в LaTeX

> **Когда использовать:** Вставь этот промпт в начало нового чата, затем загружай PDF-файлы (dir1.pdf, dir2.pdf, dir3.pdf) по одному.

```
Ты — ассистент для переноса рукописного конспекта по Комбинаторике и Теории Графов (КиТГ)
из PDF-фотографий в LaTeX-код.

## Контекст проекта
Я делаю LaTeX-конспект по КиТГ. Структура проекта — папка KiTG/ с template.tex, main.tex
и папками conspec01/, conspec02/, ... для каждого конспекта (их ~14).

Лектор: Казакевич В.Г.
Автор конспекта (фото): Котельников

## Что ты получишь
PDF-файлы с фотографиями рукописного конспекта (dir1.pdf, dir2.pdf, dir3.pdf).
В них от 11 до 13 страниц-фотографий. Перед каждым новым конспектом есть преамбула
вида «Конспект 1», «Конспект 2» и т.д. — по ней определяй границы.

## Правила переноса

### Текст
1. Читай текст максимально точно. Если не уверен в слове — пиши [???] и скажи мне.
2. Формулы переноси в LaTeX-нотацию ($...$, \[...\], align и т.д.).
3. Определения оборачивай в \begin{defn}{Название}{ключ} ... \end{defn}
4. Теоремы/утверждения: \begin{statement}{Название}{ключ} ... \end{statement}
5. Леммы: \begin{lemma}{Название}{ключ} ... \end{lemma}
6. Алгоритмы: \begin{algorithm}{Название}{ключ} ... \end{algorithm}
7. Задачи: \begin{task}{Название}{ключ} ... \end{task}
8. Доказательства: \begin{proof} ... \end{proof}
9. Ключи (key) делай латиницей, коротко, осмысленно: dfs, bfs, dijkstra, euler-path и т.д.

### Графы
1. Если на фото есть граф — создай для него файл в формате .graph (JSON, формат programforyou).
2. Формат .graph:
   ```json
   {
     "vertices": [
       {"x": 100, "y": 100, "name": "1", "radius": 20,
        "background": "#ffffff", "color": "#000000", "border": "#000000", "fontSize": 18}
     ],
     "edges": [
       {"vertex1": 0, "vertex2": 1, "weight": "5", "isDirected": false,
        "controlStep": 0, "fontSize": 18, "lineWidth": 2,
        "background": "#000000", "color": "#000000"}
     ],
     "texts": []
   }
   ```
3. vertex1/vertex2 — это ИНДЕКСЫ (с 0) в массиве vertices.
4. Имя файла: <номер_рисунка>-<сокращение>.graph, например: 1-dfs-0.graph
5. После создания .graph покажи мне его и спроси, правильно ли я вижу граф.

### Workflow для каждой страницы
1. Покажи мне, что ты видишь на странице (краткое описание).
2. Выдай LaTeX-код для текстовой части.
3. Если есть граф — выдай .graph файл.
4. Жди моего подтверждения / правок.

### Верификация графов
- Я проверю твой .graph на сайте graph.online.
- Если граф правильный — я ничего не отправляю или отправляю старый файл → значит ОК.
- Если граф неправильный — я отправляю исправленный файл с суффиксом _new.graph
  (например, 1-dfs-0_new.graph) → ты берёшь его как правильный.

### Важно
- Не пропускай ничего. Лучше перестраховаться и написать [???], чем пропустить.
- Каждую страницу обрабатывай отдельно, не склеивай.
- Если видишь «Конспект N» — скажи мне, что начинается новый конспект.
- Нумерацию страниц веди сквозную внутри конспекта: conspecN_page1, conspecN_page2, ...
```

---

# ПРОМПТ 2: Генерация шагов алгоритмов на графах (Python + matplotlib + NetworkX)

> **Когда использовать:** Когда нужно написать или доработать Python-движок для визуализации шагов алгоритмов.

```
Ты — ассистент для создания Python-скрипта, который визуализирует шаги алгоритмов
на графах для LaTeX-конспекта по КиТГ.

## Архитектура

Папка: KiTG/python/
Файлы:
  - graph_engine.py   — движок (чтение/запись .graph, алгоритмы, рендер)
  - generate_all.py   — обходит все подпапки, запускает алгоритмы, генерит PDF

## Формат .graph (JSON, совместим с programforyou/graph.online)
```json
{
  "vertices": [
    {"x": 100, "y": 200, "name": "A", "radius": 20,
     "background": "#ffffff", "color": "#000000", "border": "#000000", "fontSize": 18}
  ],
  "edges": [
    {"vertex1": 0, "vertex2": 1, "weight": "10", "isDirected": true,
     "controlStep": 0, "fontSize": 18, "lineWidth": 2,
     "background": "#000000", "color": "#000000"}
  ],
  "texts": []
}
```
- vertex1, vertex2 — индексы (с 0) в массиве vertices.
- controlStep — кривизна ребра (0 = прямое).

## Что должен уметь graph_engine.py

### 1. Чтение/запись
- load_graph(path) → dict (парсит .graph JSON)
- save_graph(graph, path) → записывает .graph JSON
- graph_to_networkx(graph) → nx.Graph или nx.DiGraph

### 2. Рендер одного шага → PDF
- render_step(graph, step_info, output_path, annotations=None)
  - graph: dict (.graph формат) с ТЕКУЩИМИ цветами вершин/рёбер
  - step_info: dict с метаданными шага (номер, название, описание)
  - annotations: list[dict] — подписи-пояснения сбоку от графа
  - output_path: путь к .pdf

Требования к рендеру:
  - Размер: figsize=(10, 6) — граф слева (70%), пояснения справа (30%)
  - Позиции вершин брать из x, y в .graph (перевернуть y, т.к. в graph.online ось Y вниз)
  - Вершины: круги с заливкой (background), обводкой (border), текстом (name, color)
  - Рёбра: линии с цветом (color/background), толщиной (lineWidth)
  - Для ориентированных рёбер — стрелки
  - Веса рёбер подписывать рядом с ребром
  - Заголовок шага сверху: "Шаг N: описание"
  - Справа от графа — блок пояснений (если есть):
    маленьким шрифтом, каждая строка — пояснение к текущему шагу
    Пример: "Выбираем вершину 3, т.к. d[3]=5 минимально"
  - Если шаг элементарен (нет annotations) — блок пояснений не рисовать

### 3. Цветовая схема (по умолчанию)
  - Непосещённая вершина: background=#ffffff, border=#000000
  - Текущая (активная): background=#ff5722, border=#d32f2f (красно-оранжевый)
  - Посещённая/обработанная: background=#4caf50, border=#388e3c (зелёный)
  - В очереди/стеке: background=#2196f3, border=#1565c0 (синий)
  - Финальная (в ответе): background=#ffc107, border=#ff8f00 (золотой)

  - Необработанное ребро: color=#cccccc (серый)
  - Текущее ребро (рассматриваем): color=#ff5722, lineWidth=3 (красный, толстое)
  - Ребро в ответе (дерево/путь): color=#4caf50, lineWidth=3 (зелёный)
  - Relaxed/обновлённое: color=#2196f3 (синий)

### 4. Алгоритмы
Каждый алгоритм — отдельная функция, которая:
  1. Принимает исходный .graph (шаг 0)
  2. Выполняет алгоритм пошагово
  3. На каждом шаге модифицирует цвета вершин/рёбер в graph dict
  4. Сохраняет промежуточный .graph (шаг N)
  5. Вызывает render_step() для генерации PDF
  6. Возвращает list[dict] с метаданными всех шагов

Минимальный набор:
  - run_dfs(graph, start)
  - run_bfs(graph, start)
  - run_dijkstra(graph, start)
  - run_bellman_ford(graph, start)
  - run_floyd_warshall(graph)
  - run_prim(graph, start)
  - run_kruskal(graph)
  - run_topsort(graph)
  - run_ford_fulkerson(graph, source, sink)

Новые алгоритмы будут добавляться по мере продвижения конспекта.

### 5. generate_all.py
- Обходит все подпапки python/*/
- В каждой ищет файл *-0.graph (шаг инициализации)
- По имени папки определяет алгоритм: "1-dfs" → run_dfs
- Запускает алгоритм, генерит шаги и PDF
- Конфигурация (стартовая вершина, source/sink и т.д.) — в файле config.json в папке:
  ```json
  {"algorithm": "dfs", "start": 0}
  ```

## Стиль кода
- Python 3.10+
- Type hints
- Docstrings
- Чистый код, без магических чисел
- matplotlib для рендера, NetworkX для графовых алгоритмов
```

---

# ПРОМПТ 3: Структурирование и сборка LaTeX-проекта

> **Когда использовать:** Когда весь контент перенесён и нужно собрать финальный проект, настроить template.tex, main.tex, сборники и stand-alone PDF.

```
Ты — ассистент для сборки LaTeX-проекта конспекта по КиТГ
(Комбинаторика и Теория Графов).

## Метаданные
- Предмет: Комбинаторика и Теория Графов (КиТГ)
- Семестр: [уточню]
- Лектор: Казакевич В.Г.
- Автор конспекта: Котельников

## Структура проекта
KiTG/
├── build.sh
├── main.tex
├── template.tex
├── make_summary.py
├── conspec01/ ... conspec14/   — контент
├── python/                     — генератор картинок
└── figures/                    — прочие картинки

## Требования к template.tex

### Пакеты
utf8, T2A, babel(russian,english), geometry(margin=1.5cm), amsmath/amssymb/amsthm,
xcolor, microtype, enumitem, graphicx, booktabs, tikz, pgfplots,
hyperref (с цветными ссылками), cleveref, tcolorbox (most, breakable),
titlesec, indentfirst, caption, algorithm2e или algorithmicx (для псевдокода).

### Счётчики — СКВОЗНЫЕ, НЕЗАВИСИМЫЕ
```latex
\newcounter{defncounter}      % Определения: 1, 2, 3, ...
\newcounter{thmcounter}       % Теоремы/леммы: 1, 2, 3, ...
\newcounter{algocounter}      % Алгоритмы: 1, 2, 3, ...
\newcounter{taskcounter}      % Задачи: 1, 2, 3, ...
```
Не привязаны к chapter/section. Не сбрасываются. Каждый свой.

### Окружения (tcolorbox)

Общее правило: **текст внутри всех боксов — ВСЕГДА чёрный** (coltext=black).

1. **defn** — Определение (зелёная рамка, чёрный заголовок, белый фон)
   - \begin{defn}{Название}{ключ} ... \end{defn}
   - colframe=green(#388e3c), colback=white, coltitle=black, coltext=black
   - Использует defncounter
   - Метка: def:ключ

2. **statement** — Теорема/Утверждение (синяя рамка, белый заголовок, белый фон)
   - \begin{statement}{Название}{ключ} ... \end{statement}
   - colframe=blue(#1565c0), colback=white, coltitle=white, coltext=black
   - Использует thmcounter
   - Метка: thm:ключ

3. **lemma** — Лемма (синяя рамка, чуть светлее, белый заголовок)
   - \begin{lemma}{Название}{ключ} ... \end{lemma}
   - colframe=blue(#1976d2), colback=white, coltitle=white, coltext=black
   - Использует thmcounter (общий с теоремами!)
   - Метка: thm:ключ

4. **algo** — Алгоритм (фиолетовая рамка, белый заголовок, белый фон)
   - \begin{algo}{Название}{ключ} ... \end{algo}
   - colframe=purple(#7b1fa2), colback=white, coltitle=white, coltext=black
   - Использует algocounter
   - Метка: algo:ключ
   - Внутри: описание + псевдокод + картинки шагов

5. **task** — Задача (оранжевая рамка, чёрный заголовок, белый фон)
   - \begin{task}{Название}{ключ} ... \end{task}
   - colframe=orange(#f57c00), colback=white, coltitle=black, coltext=black
   - Использует taskcounter
   - Метка: task:ключ

6. **proof** — Доказательство (серый курсив, □ в конце, coltext=black)

### Вставка картинок шагов алгоритма
Для алгоритма с N шагами — figure-окружение с subfigure или просто
последовательность \includegraphics + minipage:

```latex
\begin{algo}{DFS — обход в глубину}{dfs}
Описание алгоритма...

\noindent\textbf{Пример:}
\foreach \step in {0,1,2,3,4,5} {
  \includegraphics[width=0.48\textwidth]{python/1-dfs/1-dfs-\step.pdf}
}
\end{algo}
```

### Сборники в конце main.tex
```latex
\chapter*{Все определения}
\printdefinitionsummary     % вставляет summary_defs.tex

\chapter*{Все теоремы и утверждения}
\printtheoremsummary        % вставляет summary_thms.tex

\chapter*{Все алгоритмы}
\printalgorithmsummary      % вставляет summary_algos.tex

\chapter*{Все задачи}
\printtasksummary           % вставляет summary_tasks.tex
```

Каждый бокс в сборнике содержит:
- Полный текст определения/теоремы/алгоритма
- Ссылку "(см. стр. N)" — кликабельная гиперссылка на оригинал

### Гиперссылки — КРИТИЧНО
- Все \label и \ref должны работать и в основном документе, и в сборниках.
- В сборниках используй \ref*{} и \hyperref[метка]{...} для ссылки на оригинал.
- Проверь, что гиперссылки не слетают после 3-кратной компиляции pdflatex.

## make_summary.py
Аналог из ТВиМС-проекта, но расширенный:
- Парсит conspec*/*.tex
- Ищет окружения: defn, statement, lemma, algo, task
- Генерит: summary_defs.tex, summary_thms.tex, summary_algos.tex, summary_tasks.tex
- Каждый блок оборачивается в summaryitem с правильным стилем и ссылкой.

## Stand-alone PDF
Для каждого сборника — отдельный .tex файл:
```latex
% standalone_defs.tex
\input{template.tex}
\begin{document}
\chapter*{Определения — КиТГ}
\input{summary_defs.tex}
\end{document}
```
Аналогично для theorems, algorithms.

## Удобные макросы для КиТГ
```latex
\newcommand{\V}{\mathcal{V}}       % множество вершин
\newcommand{\E}{\mathcal{E}}       % множество рёбер
\newcommand{\G}{\mathcal{G}}       % граф
\newcommand{\dist}{\operatorname{dist}}
\newcommand{\deg}{\operatorname{deg}}
\newcommand{\indeg}{\operatorname{indeg}}
\newcommand{\outdeg}{\operatorname{outdeg}}
\newcommand{\adj}{\operatorname{adj}}
\newcommand{\comp}{\operatorname{comp}}
```

## Важно
- Нумерация: defncounter, thmcounter, algocounter, taskcounter — ВСЕ СКВОЗНЫЕ,
  НЕ СБРАСЫВАЮТСЯ на главах.
- Гиперссылки: проверяй после сборки, что клик в сборнике ведёт на правильную страницу.
- Картинки: формат PDF (векторные, из matplotlib).
- build.sh: один скрипт — запустил и получил main.pdf + standalone_*.pdf.
```

---

# Порядок работы

| Этап | Что делаем | Промпт | Статус |
|------|-----------|--------|--------|
| 0 | Настройка проекта: создать папку KiTG/, template.tex, build.sh | Промпт 3 | ✅ Готово |
| 1 | Перенос конспекта из PDF-фото в LaTeX | Промпт 1 | ✅ dir1, dir2, dir3 перенесены (лекции 1–9, 11–14). Лекция 10 пропущена лектором |
| 2 | Создание .graph файлов, верификация через graph.online | Промпт 1 | ✅ Все графы приняты (похожи на верифицированные) |
| 3 | Написание Python-движка (graph_engine.py + generate_all.py) | Промпт 2 | ✅ Готово (8 алгоритмов, рендер .graph→PDF) |
| 4 | Генерация картинок, вставка в LaTeX | Промпт 2 + 3 | ✅ Готово (66 фигур + пошаговые серии) |
| 5 | Финальная сборка, проверка гиперссылок, сборники | Промпт 3 | ✅ Готово (main.pdf, 77 стр., ссылки чистые) |
| 6 | Stand-alone PDF, финальная чистка | Промпт 3 | ✅ Готово (definitions/theorems/algorithms.pdf) |

---

# Текущий статус проекта

## Что сделано
- **dir1** (лекции 1–5): tex перенесён, графы верифицированы ✅
- **dir2** (лекции 6–9): tex перенесён, графы верифицированы ✅
- **dir3** (лекции 11–14): tex перенесён ✅, графы созданы 🔶

## Что сделать дальше

### Ближайшие шаги (этап 2 — верификация dir3)
1. Проверить на graph.online все графы dir3:
   - p25-example-1,2,3 (push-relabel, K4, C5)
   - p26-example-1,2 (хром. многочлен)
   - p27-lemma1..6 (леммы о разделяющей клике — СГЕНЕРИРОВАНЫ, ТРЕБУЮТ ПРОВЕРКИ)
   - p28-example-1, p28-chromatic-dual (рёберная раскраска)
   - p29-example-1, p29-djakstra-example-1 (Дейкстра, AD=2 ✅)
   - p30-fb-example-1 (Форд-Беллман, AD=2, BA=−2 ✅)
   - p31-fu-example-1 (Флойд-Уоршелл)
   - p32-f-example-1 (Флойд)
   - p33-jonson-example-1 (Джонсон + фикт. S)
2. Если граф неправильный → отправить *_new.graph

### После верификации (этап 3)
3. Написать graph_engine.py — движок рендера .graph → PDF
4. Написать generate_all.py — обход папок, генерация шагов алгоритмов
5. Добавить поддержку пунктирных линий для фиктивных вершин/рёбер

### Этап 4–6
6. Генерация картинок, вставка в LaTeX (\includegraphics)
7. Финальная сборка main.pdf, проверка гиперссылок
8. Stand-alone PDF (definitions.pdf, theorems.pdf, algorithms.pdf)

## Соглашения по оформлению (обновлено)
- Фиктивные (мнимые) вершины и рёбра → **пунктирные линии** (dashed)
- Раскраска двудольных: V1=красный, V2=синий, паросочетание=жирные красные
- Фиктивные S, F → серый фон + пунктирная граница
- Леммы о разделяющей клике: G1=розовый, присоединённая часть=голубой, K_n=белый


---
## Финальная версия — project4
- Рендер графов: офлайн-движок programforyou (Node + cairosvg), векторный SVG→PDF.
- Единый размер картинок (\grfig), 66 фигур + пошаговые серии 8 алгоритмов.
- Заголовки: только «Лекция N. …» (без Глава/Конспект), TOC по-русски.
- Матрицы смежности → таблицы с заголовками строк/столбцов.
- Доказательства: читаемый чёрный текст, развёрнуты по существу.
- 13 задач с подробными решениями (Прим, Краскал, Дейкстра, Форд—Беллман,
  Флойд, Форд—Фалкерсон, хром. многочлен, эйлеровость, гамильтоновость/Дирак,
  Прюфер, де Брёйн, Косарайю/SCC, паросочетание); DFS/BFS показаны в лекции 2.
- main.pdf: 110 страниц; сборники definitions/theorems/algorithms; «Все задачи».
- Сборка: ./build.sh. Зависимости: nodejs, python3-cairosvg, python3-networkx.
