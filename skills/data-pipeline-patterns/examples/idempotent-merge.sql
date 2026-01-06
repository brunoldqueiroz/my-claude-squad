-- Idempotent MERGE pattern for incremental loading
-- Works across: Snowflake, SQL Server, PostgreSQL (15+), BigQuery

-- ================================================
-- Snowflake MERGE
-- ================================================
MERGE INTO target.orders AS t
USING staging.orders_increment AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        t.customer_id = s.customer_id,
        t.order_date = s.order_date,
        t.total_amount = s.total_amount,
        t.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, order_date, total_amount, created_at, updated_at)
    VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

-- ================================================
-- SQL Server MERGE
-- ================================================
MERGE target.orders AS t
USING staging.orders_increment AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        t.customer_id = s.customer_id,
        t.order_date = s.order_date,
        t.total_amount = s.total_amount,
        t.updated_at = GETDATE()
WHEN NOT MATCHED BY TARGET THEN
    INSERT (order_id, customer_id, order_date, total_amount, created_at, updated_at)
    VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount, GETDATE(), GETDATE());

-- ================================================
-- PostgreSQL (15+) MERGE
-- ================================================
MERGE INTO target.orders AS t
USING staging.orders_increment AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        customer_id = s.customer_id,
        order_date = s.order_date,
        total_amount = s.total_amount,
        updated_at = NOW()
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, order_date, total_amount, created_at, updated_at)
    VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount, NOW(), NOW());

-- ================================================
-- PostgreSQL (older) INSERT ... ON CONFLICT
-- ================================================
INSERT INTO target.orders (order_id, customer_id, order_date, total_amount, created_at, updated_at)
SELECT order_id, customer_id, order_date, total_amount, NOW(), NOW()
FROM staging.orders_increment
ON CONFLICT (order_id) DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    order_date = EXCLUDED.order_date,
    total_amount = EXCLUDED.total_amount,
    updated_at = NOW();

-- ================================================
-- BigQuery MERGE
-- ================================================
MERGE target.orders AS t
USING staging.orders_increment AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
    UPDATE SET
        customer_id = s.customer_id,
        order_date = s.order_date,
        total_amount = s.total_amount,
        updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (order_id, customer_id, order_date, total_amount, created_at, updated_at)
    VALUES (s.order_id, s.customer_id, s.order_date, s.total_amount, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
