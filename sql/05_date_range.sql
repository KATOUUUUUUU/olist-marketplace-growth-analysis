SELECT
    min(order_purchase_timestamp) AS start_date,
    max(order_purchase_timestamp) AS end_date,
    count(*) AS total_orders
FROM orders;