SELECT
  p.category,
  COUNT(CASE WHEN e.event_type = 'view'        THEN 1 END)    AS views,
  COUNT(CASE WHEN e.event_type = 'add_to_cart' THEN 1 END)    AS add_to_cart,
  COUNT(CASE WHEN e.event_type = 'purchase'    THEN 1 END)    AS purchases,
  ROUND(
    COUNT(CASE WHEN e.event_type = 'add_to_cart' THEN 1 END)
    / NULLIF(COUNT(CASE WHEN e.event_type = 'view' THEN 1 END), 0)
    * 100, 1
  )                                                            AS view_to_cart_pct,
  ROUND(
    COUNT(CASE WHEN e.event_type = 'purchase'    THEN 1 END)
    / NULLIF(COUNT(CASE WHEN e.event_type = 'add_to_cart' THEN 1 END), 0)
    * 100, 1
  )                                                            AS cart_to_purchase_pct
FROM   events   e
JOIN   products p ON e.product_id = p.product_id
WHERE  YEAR(e.created_at) = 2024
GROUP  BY p.category
ORDER  BY purchases DESC;
