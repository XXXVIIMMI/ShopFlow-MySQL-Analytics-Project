WITH first_order AS (
  SELECT
    customer_id,
    DATE_FORMAT(MIN(order_date), '%Y-%m')   AS cohort
  FROM   orders
  WHERE  status != 'cancelled'
  GROUP  BY customer_id
),
activity AS (
  SELECT
    fo.cohort,
    TIMESTAMPDIFF(
      MONTH,
      STR_TO_DATE(CONCAT(fo.cohort, '-01'), '%Y-%m-%d'),
      DATE_FORMAT(o.order_date, '%Y-%m-01')
    )                                       AS period,
    COUNT(DISTINCT o.customer_id)           AS active_customers
  FROM   orders      o
  JOIN   first_order fo ON o.customer_id = fo.customer_id
  WHERE  o.status != 'cancelled'
  GROUP  BY fo.cohort, period
)
SELECT
  a.cohort,
  a.period,
  a.active_customers,
  ROUND(
    a.active_customers * 100.0 / a0.active_customers, 1
  )                                         AS retention_pct
FROM   activity a
JOIN   activity a0
  ON   a.cohort = a0.cohort AND a0.period = 0
ORDER  BY a.cohort, a.period;
