-- ============================================================
-- eCommSupport-AI
-- Commerce schema updates
-- ============================================================

USE ecomm_support;


-- ============================================================
-- 1. Add customer-facing order number
-- ============================================================

ALTER TABLE orders
ADD COLUMN order_number VARCHAR(50) NULL AFTER order_id;

ALTER TABLE orders
ADD CONSTRAINT uq_orders_order_number
UNIQUE (order_number);


-- Existing development/seed orders.
-- Adjust these if your seed data contains different order IDs.

UPDATE orders
SET order_number = 'ORD-2026-000001'
WHERE order_id = 1;

UPDATE orders
SET order_number = 'ORD-2026-000002'
WHERE order_id = 2;

UPDATE orders
SET order_number = 'ORD-2026-000003'
WHERE order_id = 3;

UPDATE orders
SET order_number = 'ORD-2026-000004'
WHERE order_id = 4;

UPDATE orders
SET order_number = 'ORD-2026-000005'
WHERE order_id = 5;


-- Once existing rows have order numbers, enforce NOT NULL.

ALTER TABLE orders
MODIFY COLUMN order_number VARCHAR(50) NOT NULL;


-- ============================================================
-- 2. Add idempotency support for order placement
-- ============================================================

ALTER TABLE orders
ADD COLUMN idempotency_key VARCHAR(100) NULL;

ALTER TABLE orders
ADD CONSTRAINT uq_orders_idempotency_key
UNIQUE (idempotency_key);