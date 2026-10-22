# Project Walkthrough

I organized this project around one question: which markets deserve more investment, and which need operational work first? Every file either helps answer that question or makes the answer reproducible.

## 1. How the Data Flows

```text
Original Olist CSVs
  -> build_database.py
  -> data/olist.duckdb
  -> numbered SQL queries
  -> Python notebook: checks, scaling, weights, recommendations
  -> export_tableau_data.py: five chart-ready CSVs
  -> build_tableau_workbook.py: portable Tableau package
```

SQL defines the rows and metrics. Python combines those metrics into a scoring framework and tests how the recommendations change. Tableau only presents the results, so a formatting change in the dashboard never changes how a metric is defined.

## 2. The SQL in Six Groups

| Files | Question | Main techniques |
| --- | --- | --- |
| 01-05 | What is in the dataset? | `SELECT`, aliases, `GROUP BY`, `COUNT`, `MIN`, `MAX`, conditional sums |
| 06-09 | How did demand and order value change? | `DATE_TRUNC`, `EXTRACT`, matched periods, distinct order counts after joins |
| 10-13 | Which categories contributed value? | Product/category joins, `LEFT JOIN`, missing translations, category-level grain |
| 14-16 | Are delivery and review metrics usable? | Null checks, date differences, conditional rates, review denominators |
| 17-19 | Where are demand and operational risks concentrated? | CTEs, state aggregation, ranking, seller-coverage limitations |
| 20 | What belongs in a fair state comparison? | January-August windows, order-level preaggregation, sample thresholds |

Each query has a defined row grain, and every rate has an explicit denominator; the definitions are in [methodology.md](methodology.md).

The query runner shows the complete result. An earlier 25-row display cap hid the last two states on screen; it never removed them from the underlying query.

## 3. The Join That Changed the Order Count

One order can have several items. After an order-to-items join, `COUNT(*)` counts joined rows rather than distinct orders. In the final state query, I first sum item prices by order and then join that one-row-per-order result back to `orders`.

I handle reviews the same way: reviews are averaged within each order before the join. Otherwise an order with several reviews would carry extra weight and inflate product value. Switching to `COUNT(DISTINCT order_id)` alone would not fix duplicated value when several one-to-many tables are joined, which is why both items and reviews are reduced to one row per order first.

## 4. The Notebook in Eleven Steps

Each code cell has a short English explanation before it.

1. Locate the project and SQL file with `pathlib`.
2. Open DuckDB read-only and return SQL results as a pandas DataFrame.
3. Inspect rows and columns.
4. Check missing values.
5. Add exploratory measures on a copy of the data.
6. Draw a log-scale scatterplot from SQL 19's broader cohort.
7. Load SQL 20's comparable-period score inputs.
8. Min-max scale six measures, reversing the direction where needed.
9. Calculate the baseline score.
10. Compare three sets of weights and their ranks.
11. Apply recommendation rules and export the final state table.

The early scatterplot is exploratory and is not the final Tableau state population. The SQL 19 view can contain 17 states, while the final scoring view contains 16, because the two use different time windows.

## 5. One Convention for Percentages

There are two valid ways to store a rate, and mixing them causes errors:

| Stored number | Convention | Display |
| ---: | --- | --- |
| 8.13 | Percentage number | Append a literal `%` |
| 0.0813 | Ratio | Apply percentage formatting |

I standardized the Tableau inputs in `outputs/tableau/` on ratios. The export script converts the original state table's `*_pct` columns into separate `*_rate` columns, and the original SQL and notebook outputs are unchanged. As a check, each ratio equals the percentage number divided by 100, and the national late rate is `7,822 / 96,203`, not an average of state percentages.

## 6. The Tableau Build

`dashboard/workbook_template.twb` preserves the structure of my first three sheets. The builder reads that XML, updates field units and captions, adds three sheets and a second dashboard, then bundles five aggregate CSVs and Hyper extracts into a `.twbx` package. The template is a build input, not a standalone deliverable.

The package has two pages:

- **Where Should Olist Grow Next?** Overall KPIs, state scores, a scale-versus-delay scatterplot, and recommended next actions.
- **Growth & Customer Experience.** A monthly trend, the ten categories with the largest combined product value in the matched windows, and late/on-time negative-review rates.

Two parameters belong only to the monthly chart: `Trend Metric` chooses orders or product value, and `Trend Year` chooses all months, 2017, or 2018. They do not filter the fixed state scoring cohort, the overall KPIs, or the category comparison.

The state scatterplot uses a log x-axis starting at 200, so proportional differences stay visible without SP pushing every other state into the left edge. Bar charts keep a zero baseline, and the opportunity-score axis ends at 100 to leave room for labels.

Rate fields use percentage formatting, currency uses BRL, and colors distinguish recommendations instead of marking every small sample as a red danger signal. The delivery/review comparison shows sample sizes in tooltips and is described as an association, not a cause.

I checked both dashboard pages and the monthly parameter switches in Tableau on October 8, 2026. A select-to-highlight action links the two state charts by `State`, clears automatically, and excludes the overall KPI sheet. Selecting SP highlighted its bar and scatter point while the overall KPIs stayed the same, and clearing the selection restored all states. This is highlighting, not filtering, so it never changes the metrics or the scoring population. Rendered tooltips were checked on October 22, 2026; see the [validation record](validation.md).

The monthly axis uses a continuous **Month-Trunc** date rather than a numeric month part. A numeric month part would merge January 2017 and January 2018 into one point when the year is All, the same difference as between `DATE_TRUNC('month', date)` and `EXTRACT(MONTH FROM date)` in SQL.

The palette uses gray for pilot/validation markets, teal for expansion candidates, orange for operational fixes, blue for the core market, and green for selective expansion. Automatic label culling is disabled in the ranking so all sixteen scores stay visible.

The JPG previews are actual Tableau presentation screenshots. The PDF is assembled from those screenshots by `build_dashboard_preview.py`, which never recalculates or redraws the analysis. After any workbook change, the images need to be refreshed before the PDF is rebuilt.

## 7. Changes Made While Packaging

- Standardized the state-specific Tableau export to ratio-valued rates.
- Kept the earlier SQL, scoring calculations, and analysis notes unchanged.
- Removed the query runner's silent 25-row display cap and switched to a read-only connection.
- Added the eleven notebook explanations.
- Added a temporary-directory rebuild test for all SQL queries, the notebook, and exports.
- Added the two-page Tableau builder with embedded data to avoid machine-specific source paths.
- Added metric documentation and a release checklist; raw records, databases, logs, and old workbook backups are excluded from Git.

## 8. The Project in Brief

> I used Olist's historical order data to ask where expansion looked worth investigating and where delivery problems should come first. I built order-level metrics in SQL, compared the same months across two years, and used Python to score sixteen states across demand, growth, customer experience, and operating proxies. I then checked the ranking under three weight sets.
>
> SP remained the core market, while PR and MG looked like stronger expansion candidates than their size alone would suggest. RJ had meaningful demand but a weaker delivery and review profile. Across the broader reviewed-order sample, late orders had a much higher negative-review rate than on-time orders, although that does not establish causation.
>
> My recommendation is a shortlist for pilots and operational investigation, not a promised return. The data lacks margin, acquisition cost, and true seller capacity, so those would be the next checks before committing budget.

The details behind the recommendation are the join duplication problem, the eight-order cohort difference, the matched growth windows, what the seller proxy misses, and why a high score is not a forecast.
