SELECT
    t.product_category_name_english AS product_category,
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    ROUND(SUM(oi.price), 2) AS revenue,
    EXTRACT(YEAR FROM o.order_purchase_timestamp) AS year

FROM orders AS o
JOIN order_items AS oi
    ON o.order_id = oi.order_id
JOIN products AS p
    ON oi.product_id = p.product_id
JOIN product_category_translation as t
    ON p.product_category_name = t.product_category_name
WHERE o.order_status = 'delivered'
    AND o.order_purchase_timestamp >= DATE '2017-01-01'
    AND o.order_purchase_timestamp < DATE '2018-09-01'
    AND t.product_category_name_english IN (
        'health_beauty', 
        'watches_gifts', 
        'bed_bath_table', 
        'sports_leisure', 
        'computers_accessories')
    AND EXTRACT(MONTH FROM o.order_purchase_timestamp) BETWEEN 1 AND 8
GROUP BY product_category, year
ORDER BY product_category, year;