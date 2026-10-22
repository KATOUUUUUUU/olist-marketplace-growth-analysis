WITH order_revenue AS (
    SELECT
        order_id,
        SUM(price) AS product_revenue
    FROM order_items
    GROUP BY order_id
),

order_level AS (
    SELECT
        o.order_id,
        c.customer_state,
        COALESCE(r.product_revenue, 0) AS product_revenue,

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
      AND o.order_delivered_customer_date IS NOT NULL
)

SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(SUM(product_revenue), 2) AS product_revenue,
    SUM(is_late) AS late_orders,
    ROUND(100.0 * AVG(is_late), 2) AS late_delivery_rate_pct

FROM order_level

GROUP BY customer_state
ORDER BY delivered_orders DESC;