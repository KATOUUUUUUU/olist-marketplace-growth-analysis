SELECT
    COUNT(*) AS delivered_orders,
    COUNT(order_delivered_customer_date) AS orders_with_customer_date,
    COUNT(order_estimated_delivery_date) AS orders_with_estimated_date
FROM orders
WHERE order_status = 'delivered'
    AND order_purchase_timestamp >= DATE '2017-01-01'
    AND order_purchase_timestamp < DATE '2018-09-01';
