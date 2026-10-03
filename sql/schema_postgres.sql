-- Reference PostgreSQL schema. The Python pipeline can create the same
-- analytical tables automatically using SQLAlchemy.

CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    cost_price NUMERIC(12,2),
    selling_price NUMERIC(12,2),
    reorder_level INTEGER
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    customer_type VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_id VARCHAR(20) PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id VARCHAR(30) PRIMARY KEY,
    sale_date DATE NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20),
    quantity INTEGER NOT NULL,
    discount_per_unit NUMERIC(12,2),
    sales_amount NUMERIC(12,2),
    payment_method VARCHAR(20),
    cost_price NUMERIC(12,2),
    revenue NUMERIC(12,2),
    cogs NUMERIC(12,2),
    gross_profit NUMERIC(12,2),
    date_id INTEGER
);
