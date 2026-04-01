SELECT
  p.name                                                       AS product,
  p.category,
  SUM(oi.quantity)                                             AS units_sold,
  ROUND(
    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)),
    2
  )                                                            AS net_revenue,
  ROUND(
    (SUM(oi.unit_price) - SUM(p.cost_price))
    / SUM(oi.unit_price) * 100,
    1
  )                                                            AS margin_pct
FROM   order_items  oi
JOIN   products     p  ON oi.product_id = p.product_id
JOIN   orders       o  ON oi.order_id   = o.order_id
WHERE  o.status          != 'cancelled'
  AND  YEAR(o.order_date) = 2024
GROUP  BY p.product_id, p.name, p.category
ORDER  BY net_revenue DESC
LIMIT  8;
