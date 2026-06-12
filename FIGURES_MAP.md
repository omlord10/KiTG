# Маппинг: графы ↔ лекции ↔ страницы
# Формат: файл.graph → лекция / страница / описание

## Лекция 1 (conspec01, стр. 1–2)
# Графов нет

## Лекция 2 (conspec02, стр. 2–5)
dfs-example.graph          → lec02 / стр.4 / Граф 12 вершин, нумерация DFS-обхода
bfs-example.graph          → lec02 / стр.4 / Тот же граф, нумерация BFS-обхода
topsort.graph              → lec02 / стр.4–5 / Исходный граф A–E для Topsort (ориент., с петлями)
topsort-result-0.graph     → lec02 / стр.5 / Результат Topsort — линейный порядок B≤A≤D≤E≤C

## Лекция 3 (conspec03, стр. 5–9)
p8-componenta-svyaznosti.graph → lec03 / стр.8 / 3 компоненты связности (9 вершин)

## Лекция 4 (conspec04, стр. 9–11)
p9-example-0.graph         → lec04 / стр.9 / Метрики: 7 вершин, R=3, D=5
p9-example-1.graph         → lec04 / стр.9 / Метрики: цикл C5, R=D=2
p10-example-1.graph        → lec04 / стр.10 / Метрики: дерево 14 вершин
p10-example-5.graph        → lec04 / стр.10 / Метрики: 11 вершин с циклами
p11-example-1.graph        → lec04 / стр.11 / k-связность: 1-связный (дерево)
p11-example-2.graph        → lec04 / стр.11 / k-связность: 1-связный (6 верш.)
p11-example-3.graph        → lec04 / стр.11 / k-связность: 3-связный (K4)
p11-example-4.graph        → lec04 / стр.11 / k-связность: 3-связный (6 верш.)
p11-example-5.graph        → lec04 / стр.11 / Мосты: 12 верш.

## Лекция 5 (conspec05, стр. 11–14, dir1 стр.11–12 + dir2 стр.1–2)
p11-example-6.graph        → lec05 / стр.11 / Изотропия/анизотропия
p12-example-1.graph        → lec05 / стр.12 / Ориент. граф (SCC) + граф Герца
p12-example-2.graph        → lec05 / стр.12 / Алг. Косарайю + граф Герца
p13-example-1.graph        → lec05 / стр.13 / Эйлеровость: пример 1 (Э)
p13-example-2.graph        → lec05 / стр.13 / Эйлеровость: пример 2 (ПЭ)
p13-example-3.graph        → lec05 / стр.13 / Эйлеровость: пример 3
p13-example-4.graph        → lec05 / стр.13 / Эйлеровость: пример 4
p13-example-5.graph        → lec05 / стр.13 / Эйлеровость: пример 5 (ни Э, ни ПЭ)
p13-example-6.graph        → lec05 / стр.13 / Эйлеровость: пример 6
p14-example-1.graph        → lec05 / стр.14 / Алг. Флёри: пример графа
p14-example-2.graph        → lec05 / стр.14 / Алг. на списках инцидентности

## Лекция 6 (conspec06, стр. 15–17, dir2 стр.3–5)
p15-example-1.graph        → lec06 / стр.15 / Полугамильтонов (путь 1–2–3–4)
p15-example-2.graph        → lec06 / стр.15 / Гамильтонов (цикл 1–2–3–4–1)
p15-example-3.graph        → lec06 / стр.15 / Ни гам., ни полугам. (1–2–3, 2–4)
p15-example-4.graph        → lec06 / стр.15 / Алг. Дирака: граф A,B,C,D,E,F
p16-example-2.graph        → lec06 / стр.16 / Граф де Брёйна B({0,1}, 2)
p17-pruffer-example-1.graph → lec06 / стр.17 / Код Прюфера: дерево 11 вершин

## Лекция 7 (conspec07, стр. 17–19, dir2 стр.5–7)
p18-example-1.graph        → lec07 / стр.18 / Обратная задача Прюфера
p19-example-1.graph        → lec07 / стр.19 / Жадный алг.: контрпример 1
p19-example-2.graph        → lec07 / стр.19 / Жадный алг.: контрпример 2
p19-prim-example-1.graph   → lec07 / стр.19 / Алг. Прима: взвешенный граф 9 вершин

## Лекция 8 (conspec08, стр. 19–21, dir2 стр.7–9)
p20-kraskal-example-1.graph    → lec08 / стр.20 / Алг. Краскала: тот же граф
p20-glavnie-circle-example-1.graph → lec08 / стр.20 / Главные циклы: граф + хорды

## Лекция 9 (conspec09, стр. 21–23, dir2 стр.9–11)
p21-example-1.graph        → lec09 / стр.21 / Двудольный: дерево 11 вершин
p21-example-2.graph        → lec09 / стр.21 / Двудольный: решётка 10 вершин
p21-example-3.graph        → lec09 / стр.21 / НЕ двудольный: треугольник
p21-example-4.graph        → lec09 / стр.21 / Критерий: чётный цикл (двудольный)
p21-example-5.graph        → lec09 / стр.21 / Критерий: нечётный цикл (не двудольный)
p22-example-1.graph        → lec09 / стр.22 / Паросочетание: не макс, не наиб.
p22-example-2.graph        → lec09 / стр.22 / Паросочетание: макс., наиб.
p22-example-3.graph        → lec09 / стр.22 / Паросочетание: макс., не наиб.
p22-example-4.graph        → lec09 / стр.22 / Паросочетание: перевёрнутый
p22-example-5.graph        → lec09 / стр.22 / Алг. наиб. паросочетания (S,A,B,C,D,α,β,γ,F)
p23-example-1.graph        → lec09 / стр.23 / Сеть: S,A,B,C,D,F + макс. поток

## Лекция 10
# Лекция пропущена лектором

## Лекция 11 (conspec11, стр. 24–25, dir3 стр.1–2)
p25-example-1.graph        → lec11 / стр.25 / Сеть Push-Relabel: S,A,B,C,D,F (ориент.)
p25-example-2.graph        → lec11 / стр.25 / Хром. число: K4 (χ=4)
p25-example-3.graph        → lec11 / стр.25 / Хром. число: C5 (χ=3)

## Лекция 12 (conspec12, стр. 26–28, dir3 стр.3–6)
p26-example-1.graph        → lec12 / стр.26 / Хром. многочлен: путь P4
p26-example-2.graph        → lec12 / стр.26 / Хром. многочлен: дерево (4 верш.)
p27-lemma1.graph           → lec12 / стр.27 / Лемма 1: висячая вершина → P_G = P_{G1}·(t−1)
p27-lemma2.graph           → lec12 / стр.27 / Лемма 2: дерево T_{n+1} → P_G = P_{G1}·(t−1)^n
p27-lemma3.graph           → lec12 / стр.27 / Лемма 3: разделяющее ребро → P_G = P_{G1}·(t−2)
p27-lemma4.graph           → lec12 / стр.27 / Лемма 4: вершина при K_n → P_G = P_{G1}·(t−n)
p27-lemma5.graph           → lec12 / стр.27 / Лемма 5: разделяющий K3 → P_G = P_{G1}·(t−1)(t−2)
p27-lemma6.graph           → lec12 / стр.27 / Лемма 6: общая, K_n → P_G = P_{G1}·P_{G2}/P_{K_n}
p28-example-1.graph        → lec12 / стр.28 / Рёберная раскраска: исходный граф G (A,B,C,D,E)
p28-chromatic-dual.graph   → lec12 / стр.28 / Хром. двойственный G_χ (AB,BC,CA,CD,BE,DB)

## Лекция 13 (conspec13, стр. 29–31, dir3 стр.6–8)
p29-example-1.graph        → lec13 / стр.29 / Граф с отриц. циклом: A,B,C,D,K
p29-djakstra-example-1.graph → lec13 / стр.29 / Алг. Дейкстры: A,B,C,D (AD=2,AC=10,DC=3,BD=7,CB=5,BA=2)
p30-fb-example-1.graph     → lec13 / стр.30 / Алг. Форда-Беллмана: тот же граф, BA=−2
p31-fu-example-1.graph     → lec13 / стр.31 / Алг. Флойда-Уоршелла: тот же граф (BA=−2)

## Лекция 14 (conspec14, стр. 32–34, dir3 стр.9–11)
p32-f-example-1.graph      → lec14 / стр.32 / Алг. Флойда: A,B,C,D (AB=1,BC=1,BD=3,CA=−2,CD=1,DA=4)
p33-jonson-example-1.graph → lec14 / стр.33 / Алг. Джонсона: тот же граф + фикт. S

---

## Соглашения по оформлению графов

### Раскраска двудольных графов
# V_1 — красный фон (red fill)
# V_2 — синий фон (blue fill)
# Рёбра паросочетания — жирные красные (bold red edges)
# Остальные рёбра — чёрные (default)
# Фиктивные вершины S, F — серый фон (grey fill)

### Фиктивные (мнимые) элементы
# Фиктивные вершины — пунктирная граница (dashed border)
# Фиктивные рёбра — пунктирная линия (dashed line)
# Примеры: вершина S в алг. Джонсона, рёбра от S ко всем вершинам

### Леммы о разделяющей клике
# G_1 — розовый фон (#ffcccc)
# Присоединённая часть — голубой фон (#ccccff)
# Разделяющая клика K_n — белый фон (#ffffff)

---

## Пошаговые демо (python/lecNN/<algo>/) — какой граф использует каждый алгоритм

# Принцип: у каждого алгоритма СВОЙ граф, структурные дубликаты не допускаются.
dfs            → dfs-example.graph            (12 вершин, lec02)
bfs            → bfs-example.graph            (тот же граф, что DFS — намеренно: сравнение обходов)
topsort        → dag-example.graph            (DAG, lec02)
bridges        → p11-example-2.graph          (lec04)
kosaraju       → p12-example-1.graph          (13 вершин, lec05)
pruefer        → p17-pruffer-example-1.graph  (дерево 11 вершин, lec06; удалённые вершины серым)
prim           → p19-prim-example-1.graph     (9 вершин, lec07, веса 1–9)
kruskal        → p20-kraskal-example-1.graph  (9 вершин, lec08, веса 1–9; ≠ граф Прима)
matching       → match-example.graph          (двудольный, lec09)
ford_fulkerson → p23-example-1.graph          (сеть S…F, lec10)
dijkstra       → p9-example-0.graph           (7 вершин, lec13; веса 1–9; БОЛЬШЕ НЕ K4!)
bellman_ford   → p30-fb-example-1.graph       (K4 с ребром BA=−2 — канонический пример лекции)

# История: раньше dijkstra и bellman_ford шли на структурно ОДИНАКОВОМ графе
# (K4 = p29-djakstra = p30-fb = p31-fu = p32-f = p11-example-3). Дейкстра
# переведена на p9-example-0; K4 остался только у Форда—Беллмана, где
# отрицательное ребро BA=−2 — суть примера.
