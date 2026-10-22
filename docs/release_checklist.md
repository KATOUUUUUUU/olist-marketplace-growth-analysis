# Release Checklist

The analysis, packaged workbook, and static previews are prepared locally. All desktop acceptance checks passed; the last tooltip check was completed on October 22, 2026. No public repository or Tableau Public upload has been created by this packaging step.

## Desktop Acceptance

- [x] Open `dashboard/olist_growth_dashboard.twbx` without a missing-source prompt.
- [x] Open both dashboard tabs; confirm no error, blank chart, clipped title, or overlapping label.
- [x] Confirm the first page shows 16 states and the KPI late rate displays as 8.13%, not 813%.
- [x] Confirm SP's score is 84.53 and its full label is visible.
- [x] Check the recommendation legend is readable in full.
- [x] Switch the monthly metric to product value, then back to orders.
- [x] Switch the year to 2017 (12 points), 2018 (8 points), and All (20 points).
- [x] Confirm category/review charts do not change; monthly parameter references exclude the KPI and state sources.
- [x] Check the review bars show 53.98% and 9.17% and category names are readable.
- [x] Inspect the late review tooltip: 7,658 reviewed orders, 4,134 negative reviews, 53.98%, and average score 2.57. Confirmed from my October 8 screenshot.
- [x] Inspect 87,902 reviewed orders in the on-time tooltip; check state/category tooltip units. Checked in Tableau Public on October 22, 2026.
- [x] Select and clear a state; confirm cross-sheet highlighting and unchanged overall KPIs. SP was tested in the native app on October 8, 2026.
- [x] Save two actual Tableau presentation screenshots and a two-page screenshot-based PDF; inspect all files. Native local image/PDF export was unavailable in this Public edition.
- [x] Add the verified images to the README and update `docs/validation.md`.

Dashboard tabs provide navigation. The state highlight action uses State matching and automatic clearing, and excludes the KPI sheet. Direct selection and clearing passed in the native app's normal window mode. Do not replace it with a global filter that mixes different source cohorts.

## Repository Review

- [x] Run `python scripts/verify_project.py` after changing analysis logic. Passed again October 8, 2026.
- [x] Run `python scripts/build_tableau_workbook.py` and `python scripts/verify_tableau_workbook.py` after changing the builder or its data inputs.
- [x] Keep raw CSVs, local databases, editor settings, logs, and older workbook backups out of the commit.
- [x] Check the README, methodology, screenshots, and workbook describe the same metric scopes.
- [x] Keep the dataset attribution and licensing notice with the derived summaries.
- [x] Review notebook outputs for personal paths before staging.

Rebuilding overwrites the generated workbook files. Preserve any manual Tableau changes in a separate working copy before running the builder; otherwise those edits will be lost.

## Publishing

On October 22, 2026, the reviewed files were published to GitHub as [olist-marketplace-growth-analysis](https://github.com/KATOUUUUUUU/olist-marketplace-growth-analysis). Only the files Git would track under `.gitignore` were uploaded; raw records, the local database, logs, and old workbook backups stayed local.

Publish the workbook to Tableau Public only when its embedded aggregate data should be public. Add the resulting public URL to the README after verifying the published view.
