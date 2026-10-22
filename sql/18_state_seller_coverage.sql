WITH seller_supply AS (
    SELECT
        seller_state AS state,
        COUNT(DISTINCT seller_id) AS seller_count
    FROM sellers
    GROUP BY seller_state
),

state_demand AS (
    SELECT
        c.customer_state AS state,
        COUNT(DISTINCT o.order_id) AS delivered_orders,
        ROUND(SUM(oi.price), 2) AS product_revenue
    FROM orders AS o
    JOIN customers AS c
        ON o.customer_id = c.customer_id
    JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= DATE '2017-01-01'
      AND o.order_purchase_timestamp < DATE '2018-09-01'
    GROUP BY c.customer_state
)

SELECT
    d.state,
    d.delivered_orders,
    d.product_revenue,
    COALESCE(s.seller_count, 0) AS sellers_in_state,

    ROUND(
        d.delivered_orders
        / NULLIF(COALESCE(s.seller_count, 0), 0),
        2
    ) AS orders_per_seller

FROM state_demand AS d
LEFT JOIN seller_supply AS s
    ON d.state = s.state

ORDER BY d.delivered_orders DESC;