WITH order_revenue AS (
    SELECT
        order_id,
        SUM(price) AS product_revenue
    FROM order_items
    GROUP BY order_id
),

seller_supply AS (
    SELECT
        seller_state AS state,
        COUNT(DISTINCT seller_id) AS seller_count
    FROM sellers
    GROUP BY seller_state
),

reviews_by_order AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM order_reviews
    GROUP BY order_id
),

order_level AS (
    SELECT
        o.order_id,
        c.customer_state,
        EXTRACT(YEAR FROM o.order_purchase_timestamp)
            AS order_year,
        COALESCE(r.product_revenue, 0)
            AS product_revenue,

        CASE
            WHEN o.order_delivered_customer_date
                 > o.order_estimated_delivery_date
            THEN 1
            ELSE 0
        END AS is_late

    FROM orders AS o

    JOIN customers AS c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_revenue AS r
        ON o.order_id = r.order_id

    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= DATE '2017-01-01'
      AND o.order_purchase_timestamp < DATE '2018-09-01'
      AND EXTRACT(MONTH FROM o.order_purchase_timestamp)
          BETWEEN 1 AND 8
      AND o.order_delivered_customer_date IS NOT NULL
),

state_metrics AS (
    SELECT
        ol.customer_state AS state,

        COUNT(*) AS delivered_orders,

        ROUND(SUM(ol.product_revenue), 2)
            AS product_revenue,

        ROUND(
            SUM(ol.product_revenue) / COUNT(*),
            2
        ) AS avg_order_value,

        SUM(ol.is_late) AS late_orders,

        ROUND(
            100.0 * AVG(ol.is_late),
            2
        ) AS late_delivery_rate_pct,

        COALESCE(MAX(ss.seller_count), 0)
            AS sellers_in_state,

        SUM(
            CASE
                WHEN ol.order_year = 2017 THEN 1
                ELSE 0
            END
        ) AS orders_2017,

        SUM(
            CASE
                WHEN ol.order_year = 2018 THEN 1
                ELSE 0
            END
        ) AS orders_2018,

        COUNT(rb.order_id) AS reviewed_orders,

        ROUND(
            AVG(rb.review_score),
            2
        ) AS avg_review_score,

        ROUND(
            100.0 * AVG(
                CASE
                    WHEN rb.order_id IS NULL THEN NULL
                    WHEN rb.review_score <= 2 THEN 1.0
                    ELSE 0.0
                END
            ),
            2
        ) AS negative_review_rate_pct

    FROM order_level AS ol

    LEFT JOIN seller_supply AS ss
        ON ol.customer_state = ss.state

    LEFT JOIN reviews_by_order AS rb
        ON ol.order_id = rb.order_id

    GROUP BY ol.customer_state
)

SELECT
    state,
    delivered_orders,
    product_revenue,
    avg_order_value,
    late_orders,
    late_delivery_rate_pct,
    sellers_in_state,
    reviewed_orders,
    avg_review_score,
    negative_review_rate_pct,
    orders_2017,
    orders_2018,

    ROUND(
        100.0 * (orders_2018 - orders_2017)
        / NULLIF(orders_2017, 0),
        2
    ) AS order_growth_pct,

    ROUND(
        delivered_orders
        / NULLIF(sellers_in_state, 0),
        2
    ) AS orders_per_seller

FROM state_metrics

WHERE delivered_orders >= 500

ORDER BY product_revenue DESC;