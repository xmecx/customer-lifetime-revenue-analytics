-- Кількість замовлень та clv на клієнта
SELECT
    o.customer_id,
    COUNT(o.order_id)        AS orders_count,
    SUM(o.amount)            AS total_revenue,
    AVG(o.amount)            AS avg_order_value
FROM orders o
GROUP BY o.customer_id;

-- Додаємо клієнтів без замовлень 
SELECT
    c.customer_id,
    COUNT(o.order_id)        AS orders_count,
    COALESCE(SUM(o.amount), 0) AS total_revenue,
    COALESCE(AVG(o.amount), 0) AS avg_order_value
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id;

-- Сегментація клієнтів за активністю
SELECT
    c.customer_id,
    COUNT(o.order_id) AS orders_count,
    CASE
        WHEN COUNT(o.order_id) = 0 THEN 'inactive'
        WHEN COUNT(o.order_id) = 1 THEN 'one_time'
        ELSE 'repeat'
    END AS customer_segment
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id;

-- Дохід по сегментах клієнтів
SELECT
    segment.customer_segment,
    COUNT(*)                  AS customer_count,
    SUM(segment.total_revenue) AS total_revenue,
    AVG(segment.total_revenue) AS avg_revenue
FROM (
    SELECT
        c.customer_id,
        CASE
            WHEN COUNT(o.order_id) = 0 THEN 'inactive'
            WHEN COUNT(o.order_id) = 1 THEN 'one_time'
            ELSE 'repeat'
        END AS customer_segment,
        COALESCE(SUM(o.amount), 0) AS total_revenue
    FROM customers c
    LEFT JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
) segment
GROUP BY segment.customer_segment;

-- VIP клієнти (Pareto)
WITH customer_revenue AS (
    SELECT
        c.customer_id,
        SUM(o.amount) AS total_revenue
    FROM customers c
    LEFT JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        total_revenue,
        NTILE(5) OVER (ORDER BY total_revenue DESC) AS revenue_group
    FROM customer_revenue
)
SELECT
    customer_id,
    total_revenue,
    CASE
        WHEN revenue_group = 1 THEN 'VIP'
        ELSE 'Regular'
    END AS vip_status
FROM ranked_customers;

-- VIP vs Regular
SELECT
    vip_status,
    COUNT(*) AS customers_count,
    SUM(total_revenue) AS total_revenue,
    AVG(total_revenue) AS avg_revenue
FROM (
    SELECT
        customer_id,
        total_revenue,
        CASE
            WHEN NTILE(5) OVER (ORDER BY total_revenue DESC) = 1
                THEN 'VIP'
            ELSE 'Regular'
        END AS vip_status
    FROM (
        SELECT
            c.customer_id,
            COALESCE(SUM(o.amount), 0) AS total_revenue
        FROM customers c
        LEFT JOIN orders o
            ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
    ) base
) vip
GROUP BY vip_status;

-- Retention/Churn
SELECT
    c.customer_id,
    MAX(o.order_date) AS last_order_date,
    CASE
        WHEN MAX(o.order_date) < DATE '2023-04-01'
             OR MAX(o.order_date) IS NULL
            THEN 'churned'
        ELSE 'active'
    END AS churn_status
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id;

-- Прогноз CLV
Avg Order Value × Avg Orders per Month × Expected Lifetime (months)
