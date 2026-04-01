-- ── 1. Monthly revenue with YoY growth ─────────────────────

SELECT
  FORMAT_DATE('%Y-%m', o.order_date)          AS month,
  ROUND(SUM(o.total_amount), 2)               AS revenue_2024,
  ROUND(prev.revenue, 2)                      AS revenue_2023,
  ROUND(
    (SUM(o.total_amount) - prev.revenue)
    / prev.revenue * 100, 1
  )                                           AS yoy_growth_pct
FROM `your-project.shopflow_db.orders` o
LEFT JOIN (
  SELECT
    FORMAT_DATE('%m', order_date)             AS mo,
    SUM(total_amount)                         AS revenue
  FROM `your-project.shopflow_db.orders`
  WHERE EXTRACT(YEAR FROM order_date) = 2023
    AND status != 'cancelled'
  GROUP BY mo
) prev
  ON FORMAT_DATE('%m', o.order_date) = prev.mo
WHERE  EXTRACT(YEAR FROM o.order_date) = 2024
  AND  o.status != 'cancelled'
GROUP  BY month, prev.revenue
ORDER  BY month;


-- ── 2. Top products by net revenue ─────────────────────────

SELECT
  p.name                                      AS product,
  p.category,
  SUM(oi.quantity)                            AS units_sold,
  ROUND(
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)),
    2
  )                                           AS net_revenue,
  ROUND(
    (SUM(oi.unit_price) - SUM(p.cost_price))
    / SUM(oi.unit_price) * 100, 1
  )                                           AS margin_pct
FROM `your-project.shopflow_db.order_items`  oi
JOIN `your-project.shopflow_db.products`     p  ON oi.product_id = p.product_id
JOIN `your-project.shopflow_db.orders`       o  ON oi.order_id   = o.order_id
WHERE  o.status != 'cancelled'
  AND  EXTRACT(YEAR FROM o.order_date) = 2024
GROUP  BY p.product_id, p.name, p.category
ORDER  BY net_revenue DESC
LIMIT  8;


-- ── 3. Customer LTV with RFM quintile ──────────────────────

SELECT
  c.name,
  c.segment,
  COUNT(DISTINCT o.order_id)                  AS total_orders,
  ROUND(SUM(o.total_amount), 2)               AS lifetime_value,
  ROUND(AVG(o.total_amount), 2)               AS avg_order_value,
  DATE_DIFF(CURRENT_DATE(), MAX(o.order_date), DAY)
                                              AS days_since_last_order,
  NTILE(5) OVER (ORDER BY SUM(o.total_amount)) AS ltv_quintile
FROM `your-project.shopflow_db.customers`    c
JOIN `your-project.shopflow_db.orders`       o ON c.customer_id = o.customer_id
WHERE  o.status != 'cancelled'
GROUP  BY c.customer_id, c.name, c.segment
ORDER  BY lifetime_value DESC
LIMIT  10;


-- ── 4. Cohort retention ─────────────────────────────────────

WITH first_order AS (
  SELECT
    customer_id,
    FORMAT_DATE('%Y-%m', MIN(order_date))     AS cohort
  FROM `your-project.shopflow_db.orders`
  WHERE status != 'cancelled'
  GROUP BY customer_id
),
activity AS (
  SELECT
    fo.cohort,
    DATE_DIFF(
      DATE_TRUNC(o.order_date, MONTH),
      PARSE_DATE('%Y-%m', fo.cohort),
      MONTH
    )                                         AS period,
    COUNT(DISTINCT o.customer_id)             AS active_customers
  FROM `your-project.shopflow_db.orders`     o
  JOIN first_order fo ON o.customer_id = fo.customer_id
  WHERE o.status != 'cancelled'
  GROUP BY fo.cohort, period
)
SELECT
  a.cohort,
  a.period,
  a.active_customers,
  ROUND(
    a.active_customers / a0.active_customers * 100, 1
  )                                           AS retention_pct
FROM   activity a
JOIN   activity a0
  ON   a.cohort = a0.cohort AND a0.period = 0
ORDER  BY a.cohort, a.period;


-- ── 5. Category conversion funnel ──────────────────────────

SELECT
  p.category,
  COUNTIF(e.event_type = 'view')              AS views,
  COUNTIF(e.event_type = 'add_to_cart')       AS add_to_cart,
  COUNTIF(e.event_type = 'purchase')          AS purchases,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(e.event_type = 'add_to_cart'),
      COUNTIF(e.event_type = 'view')
    ) * 100, 1
  )                                           AS view_to_cart_pct,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(e.event_type = 'purchase'),
      COUNTIF(e.event_type = 'add_to_cart')
    ) * 100, 1
  )                                           AS cart_to_purchase_pct
FROM `your-project.shopflow_db.events`       e
JOIN `your-project.shopflow_db.products`     p ON e.product_id = p.product_id
WHERE  EXTRACT(YEAR FROM e.created_at) = 2024
GROUP  BY p.category
ORDER  BY purchases DESC;
