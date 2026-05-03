-- ============================================================
-- DDL: Data Warehouse saleshealth_dwh
-- Esquema en estrella tipo Kimball
-- ============================================================

-- Crear esquemas
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS marts;

-- ============================================================
-- DIMENSIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_sk         SERIAL PRIMARY KEY,
    full_date       DATE NOT NULL UNIQUE,
    year            INT,
    quarter         INT,
    month           INT,
    month_name      VARCHAR(20),
    week            INT,
    day_of_month    INT,
    day_of_week     INT,
    day_name        VARCHAR(20),
    is_weekend      BOOLEAN
);

CREATE TABLE IF NOT EXISTS dwh.dim_customer (
    customer_sk     SERIAL PRIMARY KEY,
    customer_id     INT NOT NULL UNIQUE,
    first_name      VARCHAR(100),
    last_name       VARCHAR(200),
    email           VARCHAR(200),
    phone           VARCHAR(50),
    postal_code     VARCHAR(10),
    zone_name       VARCHAR(100),
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dwh.dim_product (
    product_sk      SERIAL PRIMARY KEY,
    product_id      INT NOT NULL UNIQUE,
    product_name    VARCHAR(200),
    brand_name      VARCHAR(100),
    category_name   VARCHAR(100),
    unit_price      NUMERIC(10,2),
    unit_cost       NUMERIC(10,2),
    is_cost_imputed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dwh.dim_store (
    store_sk        SERIAL PRIMARY KEY,
    store_id        INT NOT NULL UNIQUE,
    store_name      VARCHAR(200),
    address         VARCHAR(300),
    city            VARCHAR(100),
    postal_code     VARCHAR(10),
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6)
);

CREATE TABLE IF NOT EXISTS dwh.dim_offer (
    offer_sk        SERIAL PRIMARY KEY,
    offer_id        INT NOT NULL UNIQUE,
    offer_name      VARCHAR(200),
    discount_pct    NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS dwh.dim_return_reason (
    reason_sk       SERIAL PRIMARY KEY,
    reason_id       INT NOT NULL UNIQUE,
    reason_desc     VARCHAR(300)
);

-- ============================================================
-- HECHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS dwh.fact_sales (
    sale_item_sk    SERIAL PRIMARY KEY,
    date_sk         INT REFERENCES dwh.dim_date(date_sk),
    customer_sk     INT REFERENCES dwh.dim_customer(customer_sk),
    product_sk      INT REFERENCES dwh.dim_product(product_sk),
    store_sk        INT REFERENCES dwh.dim_store(store_sk),
    offer_sk        INT REFERENCES dwh.dim_offer(offer_sk),
    sale_id         INT,
    sale_item_id    INT,
    quantity        INT,
    unit_price      NUMERIC(10,2),
    unit_cost       NUMERIC(10,2),
    subtotal        NUMERIC(10,2),
    gross_margin    NUMERIC(10,2),
    is_returned     BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dwh.fact_returns (
    return_sk       SERIAL PRIMARY KEY,
    date_sk         INT REFERENCES dwh.dim_date(date_sk),
    customer_sk     INT REFERENCES dwh.dim_customer(customer_sk),
    product_sk      INT REFERENCES dwh.dim_product(product_sk),
    store_sk        INT REFERENCES dwh.dim_store(store_sk),
    reason_sk       INT REFERENCES dwh.dim_return_reason(reason_sk),
    sale_item_id    INT,
    quantity_returned INT,
    refund_amount   NUMERIC(10,2)
);

-- ============================================================
-- MART ANALÍTICO
-- ============================================================

CREATE TABLE IF NOT EXISTS marts.customer_360 (
    customer_sk             INT PRIMARY KEY REFERENCES dwh.dim_customer(customer_sk),
    customer_id             INT,
    -- CLTV
    total_revenue           NUMERIC(12,2),
    total_cost              NUMERIC(12,2),
    net_margin              NUMERIC(5,4),
    purchase_frequency      NUMERIC(8,4),
    customer_lifespan_months NUMERIC(8,2),
    cltv                    NUMERIC(12,2),
    -- RFM
    recency_days            INT,
    frequency               INT,
    monetary                NUMERIC(12,2),
    rfm_score               VARCHAR(3),
    rfm_segment             VARCHAR(50),
    -- Churn
    days_since_last_purchase INT,
    churn_score             NUMERIC(5,2),
    churn_label             VARCHAR(20),
    -- Cluster
    cluster_id              INT,
    cluster_label           VARCHAR(50)
);