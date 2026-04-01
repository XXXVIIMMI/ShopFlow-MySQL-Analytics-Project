from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# ── DB config ────────────────────────────────────────────────
# Override any value with an environment variable, e.g.:
#   export DB_HOST=localhost DB_USER=root DB_PASSWORD=secret DB_NAME=shopflow_db

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "shopflow_db"),
}

_pool = MySQLConnectionPool(pool_name="shopflow", pool_size=5, **DB_CONFIG)

app = FastAPI(
    title="ShopFlow Analytics API",
    description="E-commerce business intelligence endpoints backed by MySQL.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── DB helper ────────────────────────────────────────────────

@contextmanager
def get_db():
    con = _pool.get_connection()
    try:
        yield con
    finally:
        con.close()


def fetchall(con, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = con.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


def fetchone(con, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    cur = con.cursor(dictionary=True)
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


# ── Health ───────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health():
    with get_db() as db:
        cur = db.cursor()
        cur.execute("SELECT VERSION() AS version")
        version = cur.fetchone()[0]
        cur.close()
    return {"status": "ok", "db": DB_CONFIG["database"], "mysql_version": version}


# ── 1. KPI summary ───────────────────────────────────────────

@app.get("/kpis", tags=["overview"])
def kpis(year: int = Query(2024, description="Fiscal year")):
    """
    Top-line KPIs: total revenue, order count, AOV, and
    cancellation rate for the given year.
    """
    sql = """
        SELECT
          ROUND(SUM(CASE WHEN status != 'cancelled' THEN total_amount END), 2)
                                          AS total_revenue,
          COUNT(CASE WHEN status != 'cancelled' THEN 1 END)
                                          AS total_orders,
          ROUND(
            AVG(CASE WHEN status != 'cancelled' THEN total_amount END), 2
          )                               AS avg_order_value,
          ROUND(
            100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)
            / COUNT(*), 1
          )                               AS cancellation_rate_pct
        FROM orders
        WHERE YEAR(order_date) = %s
    """
    with get_db() as db:
        row = fetchone(db, sql, (year,))
    if not row:
        raise HTTPException(404, "No data for that year")
    return row


# ── 2. Monthly revenue ───────────────────────────────────────

@app.get("/revenue/monthly", tags=["revenue"])
def monthly_revenue(
    year: int = Query(2024),
    compare_year: int = Query(2023, description="YoY comparison year"),
):
    """Monthly revenue with optional YoY comparison."""
    sql = """
        SELECT
          DATE_FORMAT(o.order_date, '%Y-%m')  AS month,
          ROUND(SUM(o.total_amount), 2)        AS revenue,
          ROUND(MAX(prev.revenue), 2)          AS prev_revenue,
          ROUND(
            (SUM(o.total_amount) - MAX(prev.revenue))
            / NULLIF(MAX(prev.revenue), 0) * 100, 1
          )                                    AS yoy_growth_pct
        FROM orders o
        LEFT JOIN (
          SELECT
            DATE_FORMAT(order_date, '%m')      AS mo,
            SUM(total_amount)                  AS revenue
          FROM   orders
          WHERE  YEAR(order_date) = %s
            AND  status != 'cancelled'
          GROUP  BY mo
        ) prev ON DATE_FORMAT(o.order_date, '%m') = prev.mo
        WHERE  YEAR(o.order_date) = %s
          AND  o.status != 'cancelled'
        GROUP  BY month
        ORDER  BY month
    """
    with get_db() as db:
        rows = fetchall(db, sql, (compare_year, year))
    return rows


# ── 3. Revenue by category ───────────────────────────────────

@app.get("/revenue/by-category", tags=["revenue"])
def revenue_by_category(year: int = Query(2024)):
    sql = """
        SELECT
          p.category,
          ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2)
                                          AS net_revenue,
          SUM(oi.quantity)                AS units_sold
        FROM   order_items oi
        JOIN   products    p ON oi.product_id = p.product_id
        JOIN   orders      o ON oi.order_id   = o.order_id
        WHERE  o.status != 'cancelled'
          AND  YEAR(o.order_date) = %s
        GROUP  BY p.category
        ORDER  BY net_revenue DESC
    """
    with get_db() as db:
        rows = fetchall(db, sql, (year,))
    return rows


# ── 4. Top products ──────────────────────────────────────────

@app.get("/products/top", tags=["products"])
def top_products(
    year: int = Query(2024),
    limit: int = Query(10, ge=1, le=50),
    category: str | None = Query(None, description="Filter by category"),
):
    base = """
        SELECT
          p.name,
          p.category,
          SUM(oi.quantity)                AS units_sold,
          ROUND(
            SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2
          )                               AS net_revenue,
          ROUND(
            (SUM(oi.unit_price) - SUM(p.cost_price))
            / SUM(oi.unit_price) * 100, 1
          )                               AS margin_pct
        FROM   order_items oi
        JOIN   products    p ON oi.product_id = p.product_id
        JOIN   orders      o ON oi.order_id   = o.order_id
        WHERE  o.status != 'cancelled'
          AND  YEAR(o.order_date) = %s
    """
    params: list[Any] = [year]
    if category:
        base += " AND p.category = %s"
        params.append(category)
    base += " GROUP BY p.product_id, p.name, p.category ORDER BY net_revenue DESC LIMIT %s"
    params.append(limit)

    with get_db() as db:
        rows = fetchall(db, base, tuple(params))
    return rows


# ── 5. Customer LTV ──────────────────────────────────────────

@app.get("/customers/ltv", tags=["customers"])
def customer_ltv(
    limit: int = Query(20, ge=1, le=100),
    segment: str | None = Query(None),
):
    base = """
        SELECT
          c.name,
          c.segment,
          c.country,
          COUNT(DISTINCT o.order_id)      AS total_orders,
          ROUND(SUM(o.total_amount), 2)   AS lifetime_value,
          ROUND(AVG(o.total_amount), 2)   AS avg_order_value,
          DATEDIFF(NOW(), MAX(o.order_date))
                                          AS days_since_last_order
        FROM   customers c
        JOIN   orders    o ON c.customer_id = o.customer_id
        WHERE  o.status != 'cancelled'
    """
    params: list[Any] = []
    if segment:
        base += " AND c.segment = %s"
        params.append(segment)
    base += """
        GROUP  BY c.customer_id, c.name, c.segment, c.country
        ORDER  BY lifetime_value DESC
        LIMIT  %s
    """
    params.append(limit)

    with get_db() as db:
        rows = fetchall(db, base, tuple(params))
    return rows


# ── 6. Order status breakdown ────────────────────────────────

@app.get("/orders/status", tags=["orders"])
def order_status(year: int = Query(2024)):
    sql = """
        SELECT
          status,
          COUNT(*)                        AS order_count,
          ROUND(SUM(total_amount), 2)     AS total_value,
          ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)
                                          AS pct_of_orders
        FROM   orders
        WHERE  YEAR(order_date) = %s
        GROUP  BY status
        ORDER  BY order_count DESC
    """
    with get_db() as db:
        rows = fetchall(db, sql, (year,))
    return rows


# ── 7. Cohort retention ──────────────────────────────────────

@app.get("/customers/cohort-retention", tags=["customers"])
def cohort_retention():
    sql = """
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
            )                                        AS period,
            COUNT(DISTINCT o.customer_id)            AS active_customers
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
          )                                          AS retention_pct
        FROM   activity a
        JOIN   activity a0
          ON   a.cohort = a0.cohort AND a0.period = 0
        ORDER  BY a.cohort, a.period
    """
    with get_db() as db:
        rows = fetchall(db, sql)
    return rows


# ── 8. Conversion funnel ─────────────────────────────────────

@app.get("/funnel/by-category", tags=["funnel"])
def funnel_by_category(year: int = Query(2024)):
    sql = """
        SELECT
          p.category,
          SUM(CASE WHEN e.event_type = 'view'        THEN 1 ELSE 0 END) AS views,
          SUM(CASE WHEN e.event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart,
          SUM(CASE WHEN e.event_type = 'purchase'    THEN 1 ELSE 0 END) AS purchases,
          ROUND(
            100.0
            * SUM(CASE WHEN e.event_type = 'add_to_cart' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN e.event_type = 'view' THEN 1 ELSE 0 END), 0),
            1
          )                                          AS view_to_cart_pct,
          ROUND(
            100.0
            * SUM(CASE WHEN e.event_type = 'purchase'    THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN e.event_type = 'add_to_cart' THEN 1 ELSE 0 END), 0),
            1
          )                                          AS cart_to_purchase_pct
        FROM   events   e
        JOIN   products p ON e.product_id = p.product_id
        WHERE  YEAR(e.created_at) = %s
        GROUP  BY p.category
        ORDER  BY purchases DESC
    """
    with get_db() as db:
        rows = fetchall(db, sql, (year,))
    return rows
