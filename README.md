# ShopFlow - MySQL Analytics Project

Full-stack e-commerce analytics project using MySQL 8, FastAPI, and a browser dashboard.

## Project Structure

```
shopflow_mysql/
|-- .env                        # Database connection settings
|-- .venv/                      # Project virtual environment (recommended)
|-- .vscode/settings.json       # Workspace interpreter + watch settings
|-- main.py                     # FastAPI app (analytics API)
|-- seed.py                     # Creates and seeds shopflow_db
|-- dashboard.html              # Interactive analytics dashboard UI
|-- requirements.txt            # Python dependencies
|
|-- 00_schema.sql               # Core schema
|-- 01_monthly_revenue.sql      # Monthly revenue + YoY
|-- 02_top_products.sql         # Top products and margin
|-- 03_customer_ltv.sql         # Customer LTV and recency
|-- 04_cohort_retention.sql     # Cohort retention query
|-- 05_category_funnel.sql      # Category conversion funnel
|-- 01_analytics_queries.sql    # BigQuery equivalents
`-- README.md
```

## What This Project Includes

- Seeded synthetic data from 2022 through 2026
- 300 customers, products, orders, order items, and event stream records
- FastAPI endpoints for KPI, revenue, product, customer, funnel, and cohort analytics
- Dashboard with multi-page analytics views and year selector (2022-2026)

## Prerequisites

- Python 3.10+
- MySQL 8+ (local or Docker)

## Quick Start

### 1. Configure environment

Make sure your `.env` contains:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=shopflow_db
```

### 2. Create virtual environment and install dependencies

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 3. Seed database

```bash
python seed.py
```

### 4. Start API

Recommended for Linux (avoids file watch limit errors):

```bash
WATCHFILES_FORCE_POLLING=true .venv/bin/python -m uvicorn main:app --reload
```

API URLs:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

### 5. Open dashboard

Open `dashboard.html` (for example with Live Server), then verify it connects to `http://localhost:8000` in the Settings page.

## API Endpoints

- `GET /health`
- `GET /kpis?year=2026`
- `GET /revenue/monthly?year=2026&compare_year=2025`
- `GET /revenue/by-category?year=2026`
- `GET /products/top?year=2026&limit=15`
- `GET /customers/ltv?limit=20`
- `GET /orders/status?year=2026`
- `GET /customers/cohort-retention`
- `GET /funnel/by-category?year=2026`

## SQL Scripts

Run schema and analytics manually:

```bash
mysql -u root -p < 00_schema.sql
mysql -u root -p shopflow_db < 01_monthly_revenue.sql
mysql -u root -p shopflow_db < 02_top_products.sql
mysql -u root -p shopflow_db < 03_customer_ltv.sql
mysql -u root -p shopflow_db < 04_cohort_retention.sql
mysql -u root -p shopflow_db < 05_category_funnel.sql
```

## Troubleshooting

### OSError: OS file watch limit reached

Use polling mode and project interpreter:

```bash
WATCHFILES_FORCE_POLLING=true .venv/bin/python -m uvicorn main:app --reload
```

### Access denied for user root (using password: NO)

- Ensure `.env` has `DB_PASSWORD`
- Run from project root so `load_dotenv()` picks up `.env`

### Address already in use (:8000)

```bash
pkill -f "uvicorn main:app"
```

## Notes

- `seed.py` and `main.py` both load `.env` automatically.
- Demo data is available in `dashboard.html` if API is offline.

## Result

https://github.com/user-attachments/assets/7d431db5-e0d3-439b-aff0-0e26c1a08e47


