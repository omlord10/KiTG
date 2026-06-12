# KiTG — LaTeX Notes for Combinatorics & Graph Theory

LaTeX lecture notes for **Combinatorics and Graph Theory** (КиТГ) course, lectures by V.G. Kazakevich.

[English](README.md) | [Русский](README_ru.md)

## What's inside

- **110-page main PDF** with color-coded definitions, theorems, algorithms, and problems
- **Step-by-step visualizations** for 12 graph algorithms (DFS, BFS, Dijkstra, Bellman–Ford, Prim, Kruskal, TopSort, Ford–Fulkerson, Kosaraju, Bridges, Matching, Prüfer)
- **Standalone PDFs** for definitions, theorems, and algorithms (printable cheat sheets)
- **Python graph engine** that renders `.graph` files to PDF via [programforyou](https://graph.online)

## Structure

```
├── build.sh              # One-click build
├── main.tex              # Main document
├── template.tex          # Style definitions & environments
├── titlepage.tex         # Title page
├── conspec01/..14/       # Lecture content (LaTeX)
├── python/               # Graph visualization engine
│   ├── graph_engine.py   # Algorithms + .graph → PDF renderer
│   ├── generate_steps.py # Step-by-step series generator
│   ├── generate_all.py   # Batch generator
│   ├── pfy_render.py     # programforyou offline renderer
│   └── lecNN/<algo>/     # Generated step images (.graph + .pdf)
├── figures/              # Standalone graph figures
├── standalone_defs.pdf   # All definitions
├── standalone_thms.pdf   # All theorems
└── standalone_algos.pdf  # All algorithms
```

## Dependencies

| Tool | Purpose | Install (Ubuntu/Kubuntu) |
|------|---------|--------------------------|
| pdflatex | LaTeX compiler | `sudo apt install texlive-full` |
| Python 3.10+ | Graph engine | pre-installed |
| networkx | Graph algorithms | `sudo apt install python3-networkx` |
| cairosvg | SVG → PDF rendering | `sudo apt install python3-cairosvg` |
| Node.js | programforyou engine | `sudo apt install nodejs` |

Or install Python deps at once:
```bash
pip install -r python/requirements.txt --break-system-packages
```

## Build

```bash
./build.sh          # Full build (images + PDFs)
./build.sh --quick  # LaTeX only (skip image generation)
```

**Output:** `main.pdf`, `standalone_defs.pdf`, `standalone_thms.pdf`, `standalone_algos.pdf`

## Algorithms visualized

| # | Algorithm | Lecture |
|---|-----------|---------|
| 1 | DFS (Depth-First Search) | 02 |
| 2 | BFS (Breadth-First Search) | 02 |
| 3 | Dijkstra's Algorithm | 13 |
| 4 | Bellman–Ford Algorithm | 13 |
| 5 | Prim's MST | 07 |
| 6 | Kruskal's MST | 08 |
| 7 | Topological Sort (Kahn) | 02 |
| 8 | Ford–Fulkerson (Max Flow) | 10 |
| 9 | Kosaraju (SCC) | 05 |
| 10 | Bridges (DFS) | 04 |
| 11 | Maximum Matching (Kuhn) | 09 |
| 12 | Prüfer Code | 06 |

## License

This project is for educational purposes.
