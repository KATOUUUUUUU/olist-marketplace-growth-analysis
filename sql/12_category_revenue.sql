
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS product_category,
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    ROUND(SUM(oi.price), 2) AS revenue,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value



FROM orders AS o
JOIN order_items AS oi
    ON o.order_id = oi.order_id
LEFT JOIN products AS p
    ON oi.product_id = p.product_id
LEFT JOIN product_category_translation as t
    ON p.product_category_name = t.product_category_name

WHERE o.order_status = 'delivered'
    AND o.order_purchase_timestamp >= DATE '2017-01-01'
    AND o.order_purchase_timestamp < DATE '2018-09-01'

GROUP BY product_category
ORDER BY revenue DESC
LIMIT 10;
