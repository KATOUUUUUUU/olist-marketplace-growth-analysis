# Metric Definitions and Decision Rules

## Analysis Cohorts

All dates below refer to **purchase date**, not the month in which delivery occurred.

| Output | Grain | Population |
| --- | --- | --- |
| `tableau_kpis.csv` | One overall row | Delivered orders purchased January 2017-August 2018 with actual delivery dates: 96,203 |
| `tableau_monthly_trend.csv` | One purchase month | All delivered orders purchased January 2017-August 2018: 96,211 |
| `tableau_state_recommendations.csv` | One customer state | Delivered orders with actual dates, January-August in each of 2017 and 2018; states with at least 500 combined orders: 16 states |
| `tableau_category_metrics.csv` | One product category | Delivered orders, January-August in each of 2017 and 2018; 74 category groups |
| `tableau_delivery_review.csv` | Late or on-time delivery group | The KPI cohort, restricted to orders with matched reviews: 95,560 |

The monthly series contains eight delivered orders with no actual delivery date. They remain useful for demand counts but cannot be classified for delivery performance, so they are excluded from the KPI cohort. The 16-state scoring population is a different cohort and must not be labeled a national total.

## Order-Level Modeling

`orders` is the starting grain: one record per order. Joining it directly to item-level or review-level data can multiply rows. Item prices are summed by `order_id` before joining to orders; multiple review records are averaged by `order_id` before joining. Category analysis is the exception: it needs item-level category detail, with `COUNT(DISTINCT order_id)` within each category.

An order with products from two categories contributes once to each category's order count. Category order counts are therefore **not additive across categories**. Its item prices are assigned to their respective categories rather than copying its full basket value into both categories.

## Core Metrics

| Metric | Definition | Important qualification |
| --- | --- | --- |
| Delivered orders | Number of orders with status `delivered` in the stated cohort | Not all placed orders |
| Product value | Sum of `order_items.price` | BRL; excludes freight; not platform revenue or profit |
| Average order value | Product value / delivered orders | Same cohort in numerator and denominator |
| Delivery days | `DATE_DIFF('day', purchase_timestamp, actual_delivery_timestamp)` | Counts day boundaries, not elapsed hours divided by 24 |
| Late order | Actual delivery timestamp > estimated delivery timestamp | Uses stored timestamps, not date-only comparison; same-day deliveries after an estimate at midnight can qualify as late |
| Late-delivery rate | Late orders / eligible delivered orders | Actual delivery timestamp required; current KPI cohort has no missing estimated dates |
| Order review score | Mean of available review scores for the order | Multiple review rows are not counted as separate orders |
| Negative review | Order review score <= 2 | Unreviewed orders excluded from this rate's denominator |
| Growth rate | (2018 value - 2017 value) / 2017 value | January-August matched windows; zero base produces NULL, not zero growth |
| Orders per seller | Customer-state delivered orders / sellers listed in that state | Geographic proxy, not orders actually fulfilled by each seller or a capacity measure |

The historical timestamp rule is retained so the SQL, notebook, and published summaries agree. A date-only definition is a useful future sensitivity test; changing it requires recomputing the entire pipeline, not just relabeling a chart.

## Rate Units

The learning SQL and original `outputs/state_recommendations.csv` use percentage numbers in `*_pct` fields: `6.03` means 6.03%. The Tableau export layer creates a separate copy with fraction-valued `*_rate` fields: `0.0603` means 6.03%. Use Tableau's normal percentage format for those fields.

The state export converts the notebook's already rounded percentages; it does not recover unrounded source precision. Other Tableau rates are calculated directly as ratios by the exporter. Growth ratios can exceed 1. Do not apply a universal 0-1 validity check to growth.

Neither rates nor precomputed scores should be summed across states to produce a national metric. National rates require their original numerators and denominators. The workbook keeps the sources separate rather than blending mismatched aggregates.

## State Score

Within the 16-state sample, each input is min-max scaled:

```text
scaled = 100 * (value - sample_min) / (sample_max - sample_min)
```

For a constant input, the notebook assigns 50 to every state. Lower negative-review rates, lower late-delivery rates, and lower orders-per-local-seller ratios receive higher scores. Components are rounded to two decimals before weighted sums; the final score is also rounded to two decimals.

| Component | Baseline | Growth-first | Reliability-first |
| --- | ---: | ---: | ---: |
| Order scale | 25% | 20% | 20% |
| Order growth | 20% | 30% | 15% |
| Average order value | 10% | 10% | 10% |
| Customer satisfaction | 20% | 15% | 20% |
| Delivery reliability | 15% | 15% | 25% |
| Seller coverage proxy | 10% | 10% | 10% |

The score favors existing coverage rather than treating every apparent supply gap as an opportunity. Its components can be correlated, SP strongly influences the scale range, and no cost or margin input is available. A score of 84.53 is not an 84.53% probability of success. The three scenarios test chosen priorities, not statistical confidence or all possible assumptions.

## Recommendation Rules

The notebook applies these rules in order:

1. SP is designated the core market.
2. Fewer than 2,000 orders leads to `Pilot / validate data`.
3. At least 11% late delivery **or** 16% negative reviews leads to `Fix operations first`.
4. Baseline rank <= 5 and at least 3,000 orders leads to `Priority expansion`.
5. Remaining states receive `Selective expansion / monitor`.

Because the small-sample rule comes first, a pilot market can still have high operational risk. The separate `risk_flag` preserves that warning. Thresholds are screening choices, not optimized cutoffs or statistical sample-size guarantees.

## Source of Truth

- `sql/20_state_score_inputs.sql`: final state metrics and matched seasonal windows.
- `notebooks/01_state_opportunity_analysis.ipynb`: score transformations, scenarios, recommendations.
- `scripts/export_tableau_data.py`: all Tableau cohort definitions and rate-unit conversion.
- `outputs/tableau/`: chart-ready snapshots.

The earlier SQL files and exploratory notebook chart document the learning sequence. SQL 19 uses a broader period and produces a different state set, so its exploratory scatterplot should not be substituted for the final scoring view.
