USE ecomm_support;

INSERT INTO customers (first_name, last_name, email, phone) VALUES
('Anna', 'Schmidt', 'anna.schmidt@example.com', '+49-170-1000001'),
('David', 'Miller', 'david.miller@example.com', '+49-170-1000002'),
('Sofia', 'Rossi', 'sofia.rossi@example.com', '+39-320-1000003'),
('Liam', 'Taylor', 'liam.taylor@example.com', '+44-7700-100004'),
('Maya', 'Singh', 'maya.singh@example.com', '+49-170-1000005');

INSERT INTO customer_addresses
(customer_id, address_type, address_line1, address_line2, city, state, postal_code, country_code, is_default) VALUES
(1, 'HOME', 'Invalidenstrasse 10', NULL, 'Berlin', 'Berlin', '10115', 'DE', TRUE),
(1, 'WORK', 'Potsdamer Platz 5', 'Floor 7', 'Berlin', 'Berlin', '10785', 'DE', FALSE),
(2, 'HOME', 'Mainzer Landstrasse 50', NULL, 'Frankfurt', 'Hessen', '60329', 'DE', TRUE),
(3, 'HOME', 'Via Torino 21', NULL, 'Milan', 'Lombardy', '20123', 'IT', TRUE),
(4, 'HOME', '12 King Street', NULL, 'London', 'Greater London', 'SW1A 1AA', 'GB', TRUE),
(5, 'HOME', 'Leopoldstrasse 18', NULL, 'Munich', 'Bavaria', '80802', 'DE', TRUE);

INSERT INTO products
(sku, name, description, category, brand, price, currency, stock_quantity, active) VALUES
('LAP-DELL-XPS13', 'Dell XPS 13', '13-inch premium lightweight laptop, 16GB RAM, 512GB SSD.', 'Laptop', 'Dell', 1399.00, 'EUR', 12, TRUE),
('LAP-LEN-X1C', 'Lenovo ThinkPad X1 Carbon', '14-inch business laptop, 32GB RAM, 1TB SSD, lightweight chassis.', 'Laptop', 'Lenovo', 1499.00, 'EUR', 7, TRUE),
('LAP-HP-ENVY14', 'HP Envy 14', '14-inch laptop suitable for productivity and light creative work.', 'Laptop', 'HP', 1099.00, 'EUR', 0, TRUE),
('LAP-ASUS-ZEN14', 'ASUS Zenbook 14', 'Portable 14-inch OLED laptop with long battery life.', 'Laptop', 'ASUS', 1299.00, 'EUR', 18, TRUE),
('MON-DELL-U2723', 'Dell UltraSharp 27', '27-inch 4K USB-C productivity monitor.', 'Monitor', 'Dell', 649.00, 'EUR', 22, TRUE),
('HEAD-SONY-XM5', 'Sony WH-1000XM5', 'Wireless noise-cancelling headphones with long battery life.', 'Headphones', 'Sony', 349.00, 'EUR', 35, TRUE),
('HEAD-BOS-QC', 'Bose QuietComfort', 'Wireless noise-cancelling over-ear headphones.', 'Headphones', 'Bose', 329.00, 'EUR', 20, TRUE),
('MOUSE-LOG-MX3S', 'Logitech MX Master 3S', 'Ergonomic wireless productivity mouse.', 'Accessory', 'Logitech', 109.00, 'EUR', 44, TRUE),
('KEY-LOG-MX', 'Logitech MX Keys', 'Low-profile wireless productivity keyboard.', 'Accessory', 'Logitech', 119.00, 'EUR', 31, TRUE),
('CAB-USBC-2M', 'USB-C Cable 2m', 'USB-C charging and data cable, 2 meters.', 'Accessory', 'Anker', 19.99, 'EUR', 120, TRUE),
('TAB-IPADAIR', 'Apple iPad Air', 'Portable tablet with 11-inch display.', 'Tablet', 'Apple', 699.00, 'EUR', 15, TRUE),
('CAM-LOG-BRIO', 'Logitech Brio 4K', '4K webcam for conferencing and streaming.', 'Accessory', 'Logitech', 199.00, 'EUR', 25, TRUE);

INSERT INTO warranty_plans (name, duration_months, price, currency, active) VALUES
('Extended Warranty - 1 Year', 12, 99.00, 'EUR', TRUE),
('Extended Warranty - 2 Years', 24, 169.00, 'EUR', TRUE),
('Premium Protection - 3 Years', 36, 249.00, 'EUR', TRUE);

INSERT INTO orders (customer_id, order_status, total_amount, currency, order_date) VALUES
(1, 'COMPLETED', 1499.00, 'EUR', '2026-07-05 10:15:00'),
(2, 'COMPLETED', 1399.00, 'EUR', '2026-08-05 11:00:00'),
(3, 'CONFIRMED', 477.99, 'EUR', '2026-08-16 09:30:00'),
(4, 'CANCELLED', 699.00, 'EUR', '2026-08-10 13:00:00'),
(5, 'CONFIRMED', 648.00, 'EUR', '2026-08-12 08:45:00');

INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total) VALUES
(1, 2, 1, 1499.00, 1499.00),
(2, 1, 1, 1399.00, 1399.00),
(3, 6, 1, 349.00, 349.00),
(3, 10, 3, 19.99, 59.97),
(3, 8, 1, 69.02, 69.02),
(4, 11, 1, 699.00, 699.00),
(5, 5, 1, 648.00, 648.00);

INSERT INTO customer_warranties
(order_item_id, warranty_plan_id, purchase_price, valid_from, valid_until, status) VALUES
(1, 2, 169.00, '2026-07-05', '2028-07-04', 'ACTIVE');

INSERT INTO shipments
(order_id, carrier, tracking_number, current_status, shipping_address, shipped_at, estimated_delivery_at, delivered_at) VALUES
(1, 'DHL', 'DHL-DE-100001', 'DELIVERED',
 JSON_OBJECT('name','Anna Schmidt','address_line1','Invalidenstrasse 10','address_line2',NULL,'city','Berlin','state','Berlin','postal_code','10115','country_code','DE'),
 '2026-07-06 09:00:00','2026-07-08 18:00:00','2026-07-08 13:25:00'),
(2, 'DHL', 'DHL-DE-100002', 'DELIVERED',
 JSON_OBJECT('name','David Miller','address_line1','Mainzer Landstrasse 50','address_line2',NULL,'city','Frankfurt','state','Hessen','postal_code','60329','country_code','DE'),
 '2026-08-06 08:40:00','2026-08-08 18:00:00','2026-08-08 14:05:00'),
(3, 'UPS', 'UPS-IT-100003-A', 'IN_TRANSIT',
 JSON_OBJECT('name','Sofia Rossi','address_line1','Via Torino 21','address_line2',NULL,'city','Milan','state','Lombardy','postal_code','20123','country_code','IT'),
 '2026-08-17 10:00:00','2026-08-21 18:00:00',NULL),
(3, 'UPS', 'UPS-IT-100003-B', 'PACKED',
 JSON_OBJECT('name','Sofia Rossi','address_line1','Via Torino 21','address_line2',NULL,'city','Milan','state','Lombardy','postal_code','20123','country_code','IT'),
 NULL,'2026-08-23 18:00:00',NULL),
(5, 'DPD', 'DPD-DE-100005', 'DELIVERY_FAILED',
 JSON_OBJECT('name','Maya Singh','address_line1','Leopoldstrasse 18','address_line2',NULL,'city','Munich','state','Bavaria','postal_code','80802','country_code','DE'),
 '2026-08-13 07:30:00','2026-08-15 18:00:00',NULL);

INSERT INTO shipment_items (shipment_id, order_item_id, quantity) VALUES
(1,1,1),
(2,2,1),
(3,3,1),
(3,4,2),
(4,4,1),
(4,5,1),
(5,7,1);

INSERT INTO shipment_events (shipment_id, status, event_time, location, description) VALUES
(1,'PACKED','2026-07-05 18:00:00','Berlin Fulfillment Center','Order packed.'),
(1,'SHIPPED','2026-07-06 09:00:00','Berlin Fulfillment Center','Shipment handed to carrier.'),
(1,'IN_TRANSIT','2026-07-07 04:30:00','Leipzig Hub','Shipment in transit.'),
(1,'OUT_FOR_DELIVERY','2026-07-08 08:10:00','Berlin','Shipment out for delivery.'),
(1,'DELIVERED','2026-07-08 13:25:00','Berlin','Delivered to recipient.'),
(2,'PACKED','2026-08-05 17:10:00','Frankfurt Fulfillment Center','Order packed.'),
(2,'SHIPPED','2026-08-06 08:40:00','Frankfurt Fulfillment Center','Shipment handed to carrier.'),
(2,'DELIVERED','2026-08-08 14:05:00','Frankfurt','Delivered successfully.'),
(3,'PACKED','2026-08-16 16:00:00','Milan Fulfillment Center','First package packed.'),
(3,'SHIPPED','2026-08-17 10:00:00','Milan Fulfillment Center','First package shipped.'),
(3,'IN_TRANSIT','2026-08-18 03:30:00','Bologna Hub','First package in transit.'),
(4,'PACKED','2026-08-18 15:00:00','Milan Fulfillment Center','Second package packed.'),
(5,'SHIPPED','2026-08-13 07:30:00','Munich Fulfillment Center','Shipment handed to carrier.'),
(5,'IN_TRANSIT','2026-08-14 02:20:00','Nuremberg Hub','Shipment in transit.'),
(5,'OUT_FOR_DELIVERY','2026-08-15 08:00:00','Munich','Shipment out for delivery.'),
(5,'DELIVERY_FAILED','2026-08-15 14:40:00','Munich','Recipient unavailable; delivery attempt failed.');
