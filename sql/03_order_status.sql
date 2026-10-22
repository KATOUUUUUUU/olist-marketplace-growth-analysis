select order_status, count(*) as order_count
from orders
group by order_status
order by order_count desc;