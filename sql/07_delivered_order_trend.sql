SELECT
    date_trunc('month', order_purchase_timestamp) AS order_month,
    count(*) AS delivered_orders
FROM orders
WHERE order_status = 'delivered'
    AND order_purchase_timestamp >= '2017-01-01'
    AND order_purchase_timestamp < '2018-09-01'
GROUP BY order_month
ORDER BY order_month;