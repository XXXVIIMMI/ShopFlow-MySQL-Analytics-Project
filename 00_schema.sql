=CREATE DATABASE IF NOT EXISTS shopflow_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE shopflow_db;

-- ------------------------------------------------------------
-- customers
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- products
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
  product_id   INT            NOT NULL AUTO_INCREMENT,
  name         VARCHAR(200)   NOT NULL,
  category     VARCHAR(80)    NOT NULL,
  sku          VARCHAR(60)    NOT NULL UNIQUE,
  cost_price   DECIMAL(10,2)  NOT NULL,
  list_price   DECIMAL(10,2)  NOT NULL,
  PRIMARY KEY (product_id),
  INDEX idx_products_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- orders
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- order_items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- events  (clickstream / behavioural)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
