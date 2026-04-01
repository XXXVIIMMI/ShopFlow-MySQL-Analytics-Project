SELECT
  DATE_FORMAT(o.order_date, '%Y-%m')       AS month,
  ROUND(SUM(o.total_amount), 2)            AS revenue_2024,
  ROUND(prev.revenue, 2)                   AS revenue_2023,
  ROUND(
    (SUM(o.total_amount) - prev.revenue)
    / prev.revenue * 100, 1
  )                                        AS yoy_growth_pct
FROM orders o
LEFT JOIN (
  SELECT
    DATE_FORMAT(order_date, '%m')          AS mo,
    SUM(total_amount)                      AS revenue
  FROM   orders
  WHERE  YEAR(order_date) = 2023
    AND  status           != 'cancelled'
  GROUP  BY mo
) prev ON DATE_FORMAT(o.order_date, '%m') = prev.mo
WHERE  YEAR(o.order_date) = 2024
  AND  o.status           != 'cancelled'
GROUP  BY month
ORDER  BY month;
