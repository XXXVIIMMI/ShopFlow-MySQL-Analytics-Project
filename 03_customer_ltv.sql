SELECT
  c.name,
  c.segment,
  COUNT(DISTINCT o.order_id)                AS total_orders,
  ROUND(SUM(o.total_amount), 2)             AS lifetime_value,
  ROUND(AVG(o.total_amount), 2)             AS avg_order_value,
  DATEDIFF(NOW(), MAX(o.order_date))        AS days_since_last_order,
  NTILE(5) OVER (
    ORDER BY SUM(o.total_amount)
  )                                         AS ltv_quintile
FROM   customers c
JOIN   orders    o ON c.customer_id = o.customer_id
WHERE  o.status != 'cancelled'
GROUP  BY c.customer_id, c.name, c.segment
ORDER  BY lifetime_value DESC
LIMIT  10;
