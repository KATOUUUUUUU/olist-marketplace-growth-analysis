"""Export Tableau inputs with rates stored as ratios, not percentage numbers.

Use Tableau's percentage format for *_rate fields (0.0813 displays as 8.13%).
Growth rates may exceed 1; undefined growth stays NULL when the base is zero.
Money is in BRL. Round money for export, but leave ratios at calculation precision.
The original state_recommendations.csv retains its *_pct percentage numbers.
A Tableau-only copy converts those fields to ratios without changing scores.
"""

from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "olist.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tableau"


def export_query(connection, filename, query):
    output_path = OUTPUT_DIR / filename
    connection.sql(query).df().to_csv(output_path, index=False)
    print(f"Saved {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DB_PATH), read_only=True)

    export_query(
        connection,
        "tableau_kpis.csv",
        """
        WITH order_revenue AS (
            SELECT order_id, SUM(price) AS product_revenue
            FROM order_items
            GROUP BY order_id
        ),
        reviews_by_order AS (
            SELECT
                order_id,
                AVG(review_score) AS review_score
            FROM order_reviews
            GROUP BY order_id
        )
        SELECT
            DATE '2017-01-01' AS analysis_start,
            DATE '2018-08-31' AS analysis_end,
            COUNT(*) AS delivered_orders,
            ROUND(SUM(COALESCE(r.product_revenue, 0)), 2) AS product_revenue,
            ROUND(
                SUM(COALESCE(r.product_revenue, 0)) / COUNT(*),
                2
            ) AS avg_order_value,
            ROUND(
                AVG(
                    DATE_DIFF(
                        'day',
                        o.order_purchase_timestamp,
                        o.order_delivered_customer_date
                    )
                ),
                2
            ) AS avg_delivery_days,
            SUM(
                CASE
                    WHEN o.order_delivered_customer_date
                         > o.order_estimated_delivery_date
                    THEN 1
                    ELSE 0
                END
            ) AS late_orders,
            AVG(
                CASE
                    WHEN o.order_delivered_customer_date
                         > o.order_estimated_delivery_date
                    THEN 1.0
                    ELSE 0.0
                END
            ) AS late_delivery_rate,
            COUNT(rb.order_id) AS reviewed_orders,
            ROUND(AVG(rb.review_score), 2) AS avg_review_score,
            AVG(
                CASE
                    WHEN rb.review_score <= 2 THEN 1.0
                    WHEN rb.review_score IS NULL THEN NULL
                    ELSE 0.0
                END
            ) AS negative_review_rate
        FROM orders AS o
        LEFT JOIN order_revenue AS r
            ON o.order_id = r.order_id
        LEFT JOIN reviews_by_order AS rb
            ON o.order_id = rb.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp >= DATE '2017-01-01'
          AND o.order_purchase_timestamp < DATE '2018-09-01'
          AND o.order_delivered_customer_date IS NOT NULL;
        """,
    )

    export_query(
        connection,
        "tableau_monthly_trend.csv",
        """
        WITH order_revenue AS (
            SELECT order_id, SUM(price) AS product_revenue
            FROM order_items
            GROUP BY order_id
        )
        SELECT
            CAST(
                DATE_TRUNC('month', o.order_purchase_timestamp)
                AS DATE
            ) AS order_month,
            COUNT(*) AS delivered_orders,
            ROUND(SUM(COALESCE(r.product_revenue, 0)), 2) AS product_revenue,
            ROUND(
                SUM(COALESCE(r.product_revenue, 0)) / COUNT(*),
                2
            ) AS avg_order_value
        FROM orders AS o
        LEFT JOIN order_revenue AS r
            ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp >= DATE '2017-01-01'
          AND o.order_purchase_timestamp < DATE '2018-09-01'
        GROUP BY order_month
        ORDER BY order_month;
        """,
    )

    export_query(
        connection,
        "tableau_category_metrics.csv",
        """
        WITH category_year AS (
            SELECT
                COALESCE(
                    t.product_category_name_english,
                    p.product_category_name,
                    'unknown'
                ) AS product_category,
                EXTRACT(YEAR FROM o.order_purchase_timestamp) AS order_year,
                COUNT(DISTINCT o.order_id) AS delivered_orders,
                SUM(oi.price) AS product_revenue
            FROM orders AS o
            JOIN order_items AS oi
                ON o.order_id = oi.order_id
            LEFT JOIN products AS p
                ON oi.product_id = p.product_id
            LEFT JOIN product_category_translation AS t
                ON p.product_category_name = t.product_category_name
            WHERE o.order_status = 'delivered'
              AND o.order_purchase_timestamp >= DATE '2017-01-01'
              AND o.order_purchase_timestamp < DATE '2018-09-01'
              AND EXTRACT(MONTH FROM o.order_purchase_timestamp)
                  BETWEEN 1 AND 8
            GROUP BY product_category, order_year
        ),
        category_pivot AS (
            SELECT
                product_category,
                SUM(
                    CASE WHEN order_year = 2017
                         THEN delivered_orders ELSE 0 END
                ) AS orders_2017,
                SUM(
                    CASE WHEN order_year = 2018
                         THEN delivered_orders ELSE 0 END
                ) AS orders_2018,
                SUM(
                    CASE WHEN order_year = 2017
                         THEN product_revenue ELSE 0 END
                ) AS revenue_2017,
                SUM(
                    CASE WHEN order_year = 2018
                         THEN product_revenue ELSE 0 END
                ) AS revenue_2018
            FROM category_year
            GROUP BY product_category
        )
        SELECT
            product_category,
            orders_2017,
            orders_2018,
            ROUND(revenue_2017, 2) AS revenue_2017,
            ROUND(revenue_2018, 2) AS revenue_2018,
            orders_2018 - orders_2017 AS order_change,
            1.0 * (orders_2018 - orders_2017)
                / NULLIF(orders_2017, 0) AS order_growth_rate,
            ROUND(revenue_2018 - revenue_2017, 2) AS revenue_change,
            (revenue_2018 - revenue_2017)
                / NULLIF(revenue_2017, 0) AS revenue_growth_rate,
            orders_2017 + orders_2018 AS comparable_orders,
            ROUND(revenue_2017 + revenue_2018, 2)
                AS comparable_revenue
        FROM category_pivot
        ORDER BY comparable_revenue DESC;
        """,
    )

    export_query(
        connection,
        "tableau_delivery_review.csv",
        """
        WITH delivery_status AS (
            SELECT
                o.order_id,
                CASE
                    WHEN o.order_delivered_customer_date
                         > o.order_estimated_delivery_date
                    THEN 'late'
                    ELSE 'on_time'
                END AS delivery_status
            FROM orders AS o
            WHERE o.order_status = 'delivered'
              AND o.order_purchase_timestamp >= DATE '2017-01-01'
              AND o.order_purchase_timestamp < DATE '2018-09-01'
              AND o.order_delivered_customer_date IS NOT NULL
        ),
        reviews_by_order AS (
            SELECT
                order_id,
                AVG(review_score) AS review_score
            FROM order_reviews
            GROUP BY order_id
        )
        SELECT
            d.delivery_status,
            COUNT(*) AS reviewed_orders,
            ROUND(AVG(r.review_score), 2) AS avg_review_score,
            SUM(
                CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END
            ) AS negative_reviews,
            AVG(
                CASE WHEN r.review_score <= 2 THEN 1.0 ELSE 0.0 END
            ) AS negative_review_rate
        FROM delivery_status AS d
        JOIN reviews_by_order AS r
            ON d.order_id = r.order_id
        GROUP BY d.delivery_status
        ORDER BY d.delivery_status;
        """,
    )

    connection.close()

    # Keep the learning notebook's percentage-number output unchanged.
    states = pd.read_csv(PROJECT_ROOT / "outputs" / "state_recommendations.csv")
    for column in list(states.columns):
        if column.endswith("_pct"):
            target = "order_growth_rate" if column == "order_growth_pct" else column.removesuffix("_pct")
            states[target] = states.pop(column) / 100
    states.to_csv(OUTPUT_DIR / "tableau_state_recommendations.csv", index=False)
    print(f"Saved {OUTPUT_DIR / 'tableau_state_recommendations.csv'}")


if __name__ == "__main__":
    main()
