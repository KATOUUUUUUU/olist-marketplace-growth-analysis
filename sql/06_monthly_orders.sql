SELECT
    date_trunc('month', order_purchase_timestamp) as order_month,
    count(*) AS order_count
FROM orders
group by order_month
ORDER BY order_month;