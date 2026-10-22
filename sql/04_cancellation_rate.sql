select
    count(*) as total_orders,
    sum(case when order_status = 'canceled' then 1 else 0 end) as cancelled_orders,
    round(sum(case when order_status = 'canceled' then 1 else 0 end) * 100.0 / count(*), 2) as cancellation_rate
from
    orders; 