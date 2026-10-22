SELECT
    COUNT(*) AS analyzed_orders,

    ROUND(
        AVG(
            DATE_DIFF(
                'day',
                order_purchase_timestamp,
                order_delivered_customer_date
            )
        ),
        2
    ) AS avg_delivery_days,

    SUM(
        CASE
            WHEN order_delivered_customer_date
                 > order_estimated_delivery_date
            THEN 1
            ELSE 0
        END
    ) AS late_orders,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN order_delivered_customer_date
                     > order_estimated_delivery_date
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS late_delivery_rate_pct

FROM orders

WHERE order_status = 'delivered'
  AND order_purchase_timestamp >= DATE '2017-01-01'
  AND order_purchase_timestamp < DATE '2018-09-01'
  AND order_delivered_customer_date IS NOT NULL;