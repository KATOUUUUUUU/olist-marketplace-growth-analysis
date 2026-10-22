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
),

state_metrics AS (
    SELECT
        ol.customer_state AS state,
        COUNT(*) AS delivered_orders,
        ROUND(SUM(ol.product_revenue), 2) AS product_revenue,
        SUM(ol.is_late) AS late_orders,
        ROUND(100.0 * AVG(ol.is_late), 2)
            AS late_delivery_rate_pct,
        COALESCE(MAX(ss.seller_count), 0)
            AS sellers_in_state

    FROM order_level AS ol

    LEFT JOIN seller_supply AS ss
        ON ol.customer_state = ss.state

    GROUP BY ol.customer_state
),

filtered_states AS (
    SELECT
        state,
        delivered_orders,
        product_revenue,
        late_orders,
        late_delivery_rate_pct,
        sellers_in_state,

        ROUND(
            delivered_orders
            / NULLIF(sellers_in_state, 0),
            2
        ) AS orders_per_seller

    FROM state_metrics

    WHERE delivered_orders >= 500
)

SELECT
    state,
    delivered_orders,
    product_revenue,
    late_orders,
    late_delivery_rate_pct,
    sellers_in_state,
    orders_per_seller,

    RANK() OVER (
        ORDER BY delivered_orders DESC
    ) AS demand_rank,

    RANK() OVER (
        ORDER BY late_delivery_rate_pct DESC
    ) AS delay_risk_rank,

    RANK() OVER (
        ORDER BY orders_per_seller DESC NULLS LAST
    ) AS supply_gap_rank

FROM filtered_states

ORDER BY demand_rank;