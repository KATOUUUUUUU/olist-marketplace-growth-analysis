# Validation Record

Rechecked locally on October 8, 2026. This record separates data and file checks from Tableau desktop acceptance.

## Passed

| Check | Result |
| --- | --- |
| Rebuild from original CSVs in a temporary workspace | Passed |
| Execute all 20 numbered SQL queries | Passed |
| Execute all 11 notebook code cells | Passed |
| Compare regenerated state recommendations with saved output | Matched within the test tolerance |
| Compare all five regenerated Tableau CSVs with saved outputs | Matched within the test tolerance |
| KPI order count | 96,203 |
| Monthly delivered-order total | 96,211 across 20 months |
| Explain the eight-order difference | Eight delivered orders have no actual delivery timestamp |
| Missing estimates among the KPI cohort | Zero |
| Late-rate arithmetic | 7,822 / 96,203 = 0.0813072357 |
| Review cohort reconciliation | 95,560 = 7,658 late + 87,902 on-time |
| Category growth calculations | Ratios match; zero-base growth stays NULL |
| Packaged workbook sources | Five CSVs and five matching Hyper extracts |
| Hyper-to-CSV value comparison | All records match |
| Packaged source paths | Relative paths; referenced CSVs and extracts are included |
| Workbook structure | Two dashboards, six worksheets; references checked |
| Continuous month axis | Uses Month-Trunc; January 2017 and January 2018 remain separate |
| State highlight configuration | Native select action, automatic clearing, State matching, KPI sheet excluded |
| Tableau XML schema | Valid against Tableau 2026.2 schema |
| Git exclusions | Raw records, database, local editor settings, logs, stale standalone extract, and old workbooks excluded |
| Targeted path/secret-pattern scan | No personal filesystem paths or nonempty credentials found in the reviewed project text; not a comprehensive security audit |

The data rebuild was run with `python3 scripts/verify_project.py`. Package integrity was checked with `python3 scripts/verify_tableau_workbook.py`. The XML validator is provided by the local Tableau authoring tool and is not a project dependency.

## Desktop and Preview Checks

The earlier September 24 connection blocker was partly resolved on October 8. The final package opened without a missing-source prompt, and both pages were inspected in presentation mode.

| Check | Result |
| --- | --- |
| State ranking | All 16 score labels visible, including SP 84.53 |
| Recommendation legend | Full labels visible; gray pilot category; consistent colors across state charts |
| Overall KPI values | 96,203 orders, R$13,179,777.95 product value, R$137.00 AOV, 8.13% late, 12.48 delivery days |
| Monthly controls | All: 20 months; 2017: 12 months; 2018: 8 months; orders and product-value switching tested |
| Parameter scope | Category and review charts remained unchanged during monthly switches; parameters occur only in monthly calculations |
| State selection and clearing | Clicking SP in the ranking highlighted SP in both state charts; clearing restored all states |
| KPI scope during selection | All five overall KPIs stayed unchanged during the SP selection and after clearing |
| Review comparison | 53.98% and 9.17% visible; both status labels readable |
| Late review tooltip | My October 8 screenshot confirms 7,658 reviewed orders, 4,134 negative reviews, 53.98% negative-review rate, and 2.57 average score |
| Saved JPG previews | Actual Tableau presentation screenshots; both reopened and inspected |
| Two-page PDF preview | Built from the JPGs, rendered back to PNG, and visually inspected |

The tested Tableau Public app did not expose local image/PDF export commands. The JPGs are application screenshots and the PDF is a static wrapper around those images, **not a native Tableau PDF export**. No chart was redrawn to stand in for the workbook. Screenshots include the workbook tabs and show the default All/Delivered orders state.

## Tooltip Check (October 22, 2026)

The rendered tooltips were inspected in Tableau Public (Apple silicon) after reopening the packaged workbook. The package opened without a missing-source prompt.

| Tooltip | Observed |
| --- | --- |
| On-time review bar | Status on_time, average score 4.30, negative-review rate 9.17%, 8,058 negative reviews, 87,902 reviewed orders |
| State ranking (SC) | Recommendation, state, risk flag, score 45.72, 2,730 delivered orders, late rate 9.74%, negative-review rate 12.86%, order growth 122.70% |
| Category bar (health_beauty) | Product value R$ 999,246.20; orders 1,682 (2017) and 5,305 (2018); product value R$ 243,521.70 (2017) and R$ 755,724.50 (2018); growth 210.33% |

Units matched the column formats: counts with thousands separators, rates as percentages with two decimals, and BRL values with the R$ prefix. The late review tooltip had already been confirmed from my October 8 screenshot.

Before this check, the category tooltip labeled item-price sums as "Revenue 2017", "Revenue 2018", "Revenue Change", and "Revenue Growth Rate". Because product value is not Olist revenue, those captions were renamed to "Product Value 2017 (BRL)", "Product Value 2018 (BRL)", "Product Value Change (BRL)", and "Product Value Growth Rate" in `scripts/build_tableau_workbook.py` and in the generated workbook. Only the caption attributes changed; the embedded CSV and Hyper files are byte-identical to the October 8 package, and the structural checks from `verify_tableau_workbook.py` that do not need the Hyper API passed. The full builder and `verify_tableau_workbook.py` were not rerun on October 22 because the environment used for that check lacked `duckdb` and `tableauhyperapi`.

The status bar can show Tableau's temporary sum of the two group rates (63.15%) when both review marks are selected. It is not the overall negative-review rate and must not be reported as one.

Public Tableau publishing and GitHub push are deliberately not performed by this check.

## Tested Environment

Python 3.14.6 on macOS. Packages observed in the successful local runs:

```text
duckdb==1.5.4
pandas==3.0.3
nbformat==5.10.4
nbclient==0.11.0
jupyterlab==4.6.1
matplotlib==3.11.0
seaborn==0.13.2
plotly==6.8.0
ipykernel==7.3.0
tableauhyperapi==0.0.26479
lxml==6.1.1
```

The requirements files list direct dependencies rather than a full cross-platform lockfile. A fresh environment and a different Tableau version have not been independently tested. The generated workbook uses Tableau 2026.2 XML; an older desktop release may require upgrading or a compatible export.
