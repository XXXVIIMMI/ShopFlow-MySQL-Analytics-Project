import os, random, datetime, hashlib
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}
DB_NAME = os.getenv("DB_NAME", "shopflow_db")

# ── Seed data ────────────────────────────────────────────────
random.seed(42)

PRODUCTS = [
    ("iPhone 15 Pro",       "Electronics", 820,  1199),
    ("Samsung QLED TV",     "Electronics", 620,   899),
    ("Nike Air Max",        "Apparel",      42,    95),
    ("MacBook Air M3",      "Electronics", 980,  1399),
    ("Dyson V15",           "Home",        230,   450),
    ("Sony WH-1000XM5",    "Electronics",  80,   150),
    ("Instant Pot 7-in-1", "Home",          45,    89),
    ("LG OLED Monitor",    "Electronics",  380,   649),
    ("Levi's 501 Jeans",    "Apparel",      28,    70),
    ("La Mer Moisturizer",  "Beauty",        80,   195),
    ("Vitamix Blender",     "Home",        180,   399),
    ("Fenty Beauty Set",    "Beauty",        35,    80),
    ("Kindle Paperwhite",   "Electronics",  70,   140),
    ("Allbirds Runner",     "Apparel",      60,   120),
    ("Nespresso Vertuo",    "Home",          90,   180),
]
SEGMENTS    = ["New", "Regular", "Premium", "VIP"]
STATUSES    = ["delivered", "delivered", "delivered", "shipped", "processing", "cancelled"]
SHIPPING    = ["standard", "express", "overnight"]
COUNTRIES   = ["US", "US", "US", "UK", "CA", "AU", "BD", "DE"]
FIRST_NAMES = ["Sarah","James","Priya","Chen","Maria","Alex","Fatima","David",
                "Emma","Rafi","Lena","Omar","Yuna","Carlos","Amara","Ethan",
                "Nusrat","Tahmina","Farhana","Jannat","Ayesha","Mim","Sharmeen","Sadia",
                "Nafisa","Rashid","Sabbir","Tanvir","Nayeem","Sakib","Mahin","Arif"]
LAST_NAMES  = ["Mitchell","Okafor","Sharma","Wei","Santos","Thompson","Al-Rashid",
               "Kim","Clarke","Islam","Müller","Hassan","Park","Lopez","Diallo","Brown",
               "Rahman","Ahmed","Hossain","Khan","Chowdhury","Sultana","Begum","Karim",
               "Uddin","Miah","Akter","Hasan"]
EVENT_TYPES = ["view","view","view","add_to_cart","add_to_cart","purchase"]
FRIEND_NAMES = [
    "Aabid Hasan",
    "Sajib Khan",
    "Zahidul Islam",
    "Nazirul Islam Ifran",
    "Maidul Islam Murad",
    "Azahr Uddin",
    "Sheikh Pranto",
]

def random_date(start, end):
    delta = end - start
    return start + datetime.timedelta(days=random.randint(0, delta.days))

# ── Connect and create DB ────────────────────────────────────
print(f"Connecting to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")
con = mysql.connector.connect(**DB_CONFIG)
cur = con.cursor()

cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute(f"USE `{DB_NAME}`")
print(f"Database `{DB_NAME}` ready.")

# ── Schema ───────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS events")
cur.execute("DROP TABLE IF EXISTS order_items")
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("DROP TABLE IF EXISTS products")
cur.execute("DROP TABLE IF EXISTS customers")

cur.execute("""
CREATE TABLE customers (
  customer_id  INT            NOT NULL AUTO_INCREMENT,
  name         VARCHAR(120)   NOT NULL,
  email        VARCHAR(254)   NOT NULL UNIQUE,
  segment      ENUM('New','Regular','Premium','VIP') NOT NULL DEFAULT 'New',
  signup_date  DATE           NOT NULL,
  country      VARCHAR(60)    NOT NULL DEFAULT 'US',
  is_active    TINYINT(1)     NOT NULL DEFAULT 1,
  PRIMARY KEY (customer_id),
  INDEX idx_customers_segment (segment),
  INDEX idx_customers_signup  (signup_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

cur.execute("""
CREATE TABLE products (
  product_id   INT            NOT NULL AUTO_INCREMENT,
  name         VARCHAR(200)   NOT NULL,
  category     VARCHAR(80)    NOT NULL,
  sku          VARCHAR(60)    NOT NULL UNIQUE,
  cost_price   DECIMAL(10,2)  NOT NULL,
  list_price   DECIMAL(10,2)  NOT NULL,
  PRIMARY KEY (product_id),
  INDEX idx_products_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

cur.execute("""
CREATE TABLE orders (
  order_id        INT            NOT NULL AUTO_INCREMENT,
  customer_id     INT            NOT NULL,
  order_date      DATE           NOT NULL,
  status          ENUM('processing','shipped','delivered','cancelled') NOT NULL DEFAULT 'processing',
  total_amount    DECIMAL(12,2)  NOT NULL,
  shipping_method VARCHAR(60),
  discount_code   VARCHAR(40),
  PRIMARY KEY (order_id),
  INDEX idx_orders_customer (customer_id),
  INDEX idx_orders_date     (order_date),
  INDEX idx_orders_status   (status),
  CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

cur.execute("""
CREATE TABLE order_items (
  item_id      INT            NOT NULL AUTO_INCREMENT,
  order_id     INT            NOT NULL,
  product_id   INT            NOT NULL,
  quantity     INT            NOT NULL DEFAULT 1,
  unit_price   DECIMAL(10,2)  NOT NULL,
  discount_pct DECIMAL(5,4)   NOT NULL DEFAULT 0,
  PRIMARY KEY (item_id),
  INDEX idx_items_order   (order_id),
  INDEX idx_items_product (product_id),
  CONSTRAINT fk_items_order
    FOREIGN KEY (order_id)   REFERENCES orders   (order_id),
  CONSTRAINT fk_items_product
    FOREIGN KEY (product_id) REFERENCES products (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")

cur.execute("""
CREATE TABLE events (
  event_id    BIGINT       NOT NULL AUTO_INCREMENT,
  session_id  VARCHAR(64)  NOT NULL,
  customer_id INT,
  event_type  VARCHAR(40)  NOT NULL,
  product_id  INT,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id),
  INDEX idx_events_customer  (customer_id),
  INDEX idx_events_product   (product_id),
  INDEX idx_events_type_date (event_type, created_at),
  CONSTRAINT fk_events_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_events_product
    FOREIGN KEY (product_id)  REFERENCES products  (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
con.commit()
print("Schema created.")

# ── Products ─────────────────────────────────────────────────
product_rows = []
for i, (name, cat, cost, price) in enumerate(PRODUCTS, 1):
    sku = "SKU-" + hashlib.md5(name.encode()).hexdigest()[:8].upper()
    product_rows.append((i, name, cat, sku, cost, price))

cur.executemany(
    "INSERT INTO products (product_id, name, category, sku, cost_price, list_price) VALUES (%s,%s,%s,%s,%s,%s)",
    product_rows
)
con.commit()

# Build price lookup
prices = {row[0]: row[5] for row in product_rows}

# ── Customers ────────────────────────────────────────────────
start_2022 = datetime.date(2022, 1, 1)
end_2026   = datetime.date(2026, 12, 31)
customer_rows = []
customer_meta = {}   # cid -> (segment, signup_date)

for cid in range(1, 301):
    if cid <= len(FRIEND_NAMES):
        full_name = FRIEND_NAMES[cid - 1]
    else:
        fn  = random.choice(FIRST_NAMES)
        ln  = random.choice(LAST_NAMES)
        full_name = f"{fn} {ln}"
    seg = "VIP" if cid <= len(FRIEND_NAMES) else random.choices(SEGMENTS, weights=[20, 45, 25, 10])[0]
    sd  = random_date(start_2022, end_2026)
    em  = f"{full_name.lower().replace(' ', '.')}" + f"{cid}@example.com"
    country = random.choice(COUNTRIES)
    customer_rows.append((cid, full_name, em, seg, sd.isoformat(), country, 1))
    customer_meta[cid] = (seg, sd)

cur.executemany(
    "INSERT INTO customers (customer_id, name, email, segment, signup_date, country, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s)",
    customer_rows
)
con.commit()
print("Customers inserted.")

# ── Orders, order_items, events ──────────────────────────────
order_rows  = []
item_rows   = []
event_rows  = []
oid = 1; iid = 1; eid = 1

for cid in range(1, 301):
    seg, signup = customer_meta[cid]
    n_orders = {"New": 2, "Regular": 8, "Premium": 18, "VIP": 35}[seg]
    n_orders = max(1, n_orders + random.randint(-2, 4))
    if cid <= len(FRIEND_NAMES):
        n_orders += random.randint(8, 14)
    start = max(datetime.date(2022, 1, 1), signup)

    for _ in range(n_orders):
        odate  = random_date(start, end_2026)
        status = random.choices(STATUSES, weights=[6, 6, 6, 2, 1, 1])[0]
        ship   = random.choice(SHIPPING)
        disc   = random.choice([None, None, None, "SAVE10", "VIP20"])
        n_items = random.randint(1, 4)
        pids = random.sample(range(1, len(PRODUCTS) + 1), k=min(n_items, len(PRODUCTS)))

        total = 0.0
        for pid in pids:
            qty  = random.randint(1, 3)
            dpct = 0.10 if disc else 0.0
            price = prices[pid]
            total += price * qty * (1 - dpct)
            item_rows.append((iid, oid, pid, qty, round(price, 2), dpct))
            iid += 1

        order_rows.append((oid, cid, odate.isoformat(), status, round(total, 2), ship, disc))

        # Events
        dt = datetime.datetime.combine(odate, datetime.time(0, 0))
        for pid in pids:
            for et in random.sample(EVENT_TYPES, k=random.randint(1, 4)):
                ts = dt.replace(
                    hour=random.randint(8, 22),
                    minute=random.randint(0, 59)
                )
                event_rows.append((eid, f"sess-{oid}-{pid}", cid, et, pid, ts.strftime("%Y-%m-%d %H:%M:%S")))
                eid += 1

        oid += 1

    # Batch insert every 100 customers to manage memory
    if cid % 100 == 0:
        cur.executemany(
            "INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, shipping_method, discount_code) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            order_rows
        )
        cur.executemany(
            "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct) VALUES (%s,%s,%s,%s,%s,%s)",
            item_rows
        )
        cur.executemany(
            "INSERT INTO events (event_id, session_id, customer_id, event_type, product_id, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
            event_rows
        )
        con.commit()
        print(f"  Committed up to customer {cid} ...")
        order_rows = []; item_rows = []; event_rows = []

# Final flush
if order_rows:
    cur.executemany(
        "INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, shipping_method, discount_code) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        order_rows
    )
    cur.executemany(
        "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount_pct) VALUES (%s,%s,%s,%s,%s,%s)",
        item_rows
    )
    cur.executemany(
        "INSERT INTO events (event_id, session_id, customer_id, event_type, product_id, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
        event_rows
    )
    con.commit()

cur.close()
con.close()
print(f"\nDone — {oid-1} orders, {iid-1} items, {eid-1} events, 300 customers.")
print(f"Database: `{DB_NAME}` on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
