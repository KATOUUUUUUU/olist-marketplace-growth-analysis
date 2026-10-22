"""Rebuild the learning pipeline in a temporary directory and verify its outputs."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

import duckdb
import nbformat
from nbclient import NotebookClient
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="olist-verify-") as temp:
        work = Path(temp)
        for folder in ("scripts", "sql", "notebooks"):
            shutil.copytree(ROOT / folder, work / folder)
        (work / "data").mkdir()
        (work / "data/raw").symlink_to(ROOT / "data/raw", target_is_directory=True)
        (work / "outputs/tableau").mkdir(parents=True)
        subprocess.run([sys.executable, "scripts/build_database.py"], cwd=work, check=True)
        nb = nbformat.read(work / "notebooks/01_state_opportunity_analysis.ipynb", as_version=4)
        NotebookClient(nb, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(work)}}).execute()
        subprocess.run([sys.executable, "scripts/export_tableau_data.py"], cwd=work, check=True)
        expected = pd.read_csv(ROOT / "outputs/state_recommendations.csv")
        actual = pd.read_csv(work / "outputs/state_recommendations.csv")
        pd.testing.assert_frame_equal(expected, actual, check_exact=False, rtol=1e-10)
        for file in (ROOT / "outputs/tableau").glob("*.csv"):
            pd.testing.assert_frame_equal(pd.read_csv(file), pd.read_csv(work / "outputs/tableau" / file.name), check_exact=False, rtol=1e-10)
        k = pd.read_csv(work / "outputs/tableau/tableau_kpis.csv").iloc[0]
        assert k.delivered_orders == 96203 and k.late_orders == 7822
        assert abs(k.late_delivery_rate - k.late_orders / k.delivered_orders) < 1e-12
        m = pd.read_csv(work / "outputs/tableau/tableau_monthly_trend.csv")
        assert len(m) == 20 and m.delivered_orders.sum() == 96211
        d = pd.read_csv(work / "outputs/tableau/tableau_delivery_review.csv")
        assert d.reviewed_orders.sum() == k.reviewed_orders
        assert ((d.negative_reviews / d.reviewed_orders - d.negative_review_rate).abs() < 1e-12).all()
        c = pd.read_csv(work / "outputs/tableau/tableau_category_metrics.csv")
        for kind in ("order", "revenue"):
            base = c.orders_2017 if kind == "order" else c.revenue_2017
            end = c.orders_2018 if kind == "order" else c.revenue_2018
            mask = base > 0
            assert ((c.loc[mask, kind + "_growth_rate"] - (end[mask] - base[mask]) / base[mask]).abs() < 1e-7).all()
            assert c.loc[~mask, kind + "_growth_rate"].isna().all()
        with duckdb.connect(str(work / "data/olist.duckdb"), read_only=True) as con:
            for sql in sorted((work / "sql").glob("*.sql")):
                con.sql(sql.read_text()).fetchall()
            missing = con.execute("""SELECT COUNT(*) FROM orders WHERE order_status='delivered'
                AND order_purchase_timestamp >= DATE '2017-01-01'
                AND order_purchase_timestamp < DATE '2018-09-01'
                AND order_delivered_customer_date IS NULL""").fetchone()[0]
            assert missing == 8
            missing_estimates = con.execute("""SELECT COUNT(*) FROM orders WHERE order_status='delivered'
                AND order_purchase_timestamp >= DATE '2017-01-01'
                AND order_purchase_timestamp < DATE '2018-09-01'
                AND order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NULL""").fetchone()[0]
            assert missing_estimates == 0
        report = {"status": "passed", "sql_queries": 20, "notebook_code_cells": 11,
                  "state_rows": len(actual), "monthly_rows": len(m), "category_rows": len(c),
                  "kpi_orders": int(k.delivered_orders), "monthly_orders": int(m.delivered_orders.sum()),
                  "missing_actual_delivery_dates": missing, "missing_estimated_dates_in_kpi": missing_estimates,
                  "late_delivery_rate": float(k.late_delivery_rate),
                  "state_output_matches": True, "tableau_exports_match": True}
        print(json.dumps(report, indent=2))
        return report


if __name__ == "__main__":
    main()
