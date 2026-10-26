# Power BI build kit

This folder contains the Power Query source and DAX measures needed to build the dashboard in Power BI Desktop. The source file is `../data/benchmark_scores.csv`.

## Import
1. In Power BI Desktop, choose **Get data > Blank query**.
2. Open **Advanced Editor**, paste `PowerQuery.m`, and change the CSV path to the local `data/benchmark_scores.csv` path.
3. Name the resulting table `BenchmarkScores` and load it.
4. Add the measures from `Measures.dax`.

## Model
Use one fact table (`BenchmarkScores`) at the grain of one model × benchmark. Keep `score` and `max_score` numeric. Set `release_date` to Date. Use `score_pct` only for within-benchmark ranking or display; do not aggregate it across benchmarks. The report filters should use benchmark, benchmark type, organization and release date.

## Report pages
### Overview
- KPI cards: distinct models, organizations, benchmarks and score records.
- Bar chart: model score percentage by benchmark, sorted descending; benchmark slicer is required.
- Line chart: average score percentage by release year, filtered to one benchmark.
- Table: model, organization, release date, score, maximum score and score percentage.
- Slicers: benchmark, benchmark type, organization, release date.

### Coverage
- Bar chart: models reported by benchmark, with total model count in tooltip.
- Matrix: organization × benchmark with count of reported model scores.
- Coverage percentage card, responding to benchmark filters.

Add a visible note to the report: “Scores are comparable only within the same benchmark. Chatbot Arena ELO is a rating scale. Dataset provenance and evaluation conditions were not supplied.”

## Visual previews

These static previews use the supplied CSV values to show the intended two-page report. They are not captures from Power BI Desktop. Recreate the interactive report in Power BI Desktop using the query and measures above.

![Overview page preview](screenshots/overview.png)

![Coverage page preview](screenshots/coverage.png)

To regenerate the images with Python and Pillow:

```bash
python powerbi/make_previews.py
```

