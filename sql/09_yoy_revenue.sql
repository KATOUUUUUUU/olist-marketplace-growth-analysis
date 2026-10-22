SELECT
    EXTRACT(YEAR FROM o.order_purchase_timestamp) AS order_year,
    COUNT(DISTINCT(o.order_id)) AS delivered_orders,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(SUM(oi.price) / COUNT(DISTINCT(o.order_id)), 2) AS avg_order_value
FROM orders as o
JOIN order_items as oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
AND o.order_purchase_timestamp >= '2017-01-01'
AND o.order_purchase_timestamp < '2018-09-01'
AND EXTRACT(MONTH FROM o.order_purchase_timestamp) BETWEEN 1 AND 8
GROUP BY order_year
ORDER BY order_year;