-- =============================================================================
-- Dabba: Online Food Ordering System - Database Views (MySQL 8)
-- =============================================================================

USE dabba_db;

DROP VIEW IF EXISTS top_selling_items;
DROP VIEW IF EXISTS restaurant_revenue;
DROP VIEW IF EXISTS customer_order_summary;

-- -----------------------------------------------------------------------------
-- VIEW 1: top_selling_items
-- Aggregates item sales across completed orders with restaurant context
-- -----------------------------------------------------------------------------
CREATE VIEW top_selling_items AS
SELECT 
    m.item_id,
    m.name AS item_name,
    c.name AS category_name,
    m.is_veg,
    m.price AS current_price,
    r.restaurant_id,
    r.name AS restaurant_name,
    COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
    COALESCE(SUM(oi.item_total), 0.00) AS total_sales_amount,
    COUNT(DISTINCT oi.order_id) AS orders_count
FROM menu_items m
JOIN categories c ON m.category_id = c.category_id
JOIN restaurants r ON m.restaurant_id = r.restaurant_id
LEFT JOIN order_items oi ON m.item_id = oi.item_id
LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_status = 'Delivered'
GROUP BY m.item_id, m.name, c.name, m.is_veg, m.price, r.restaurant_id, r.name;

-- -----------------------------------------------------------------------------
-- VIEW 2: restaurant_revenue
-- Summarizes financial performance, order counts, and averages per restaurant
-- -----------------------------------------------------------------------------
CREATE VIEW restaurant_revenue AS
SELECT 
    r.restaurant_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    r.rating,
    COUNT(o.order_id) AS total_orders_received,
    COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS completed_orders,
    COUNT(CASE WHEN o.order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
    COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.subtotal ELSE 0 END), 0.00) AS gross_food_sales,
    COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.discount_amount ELSE 0 END), 0.00) AS total_discounts,
    COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE 0 END), 0.00) AS net_revenue,
    COALESCE(AVG(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE NULL END), 0.00) AS avg_order_value
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.name, r.cuisine_type, r.rating;

-- -----------------------------------------------------------------------------
-- VIEW 3: customer_order_summary
-- Provides a 360-degree view of customer spending, order frequency, and loyalty
-- -----------------------------------------------------------------------------
CREATE VIEW customer_order_summary AS
SELECT 
    c.customer_id,
    u.user_id,
    u.full_name AS customer_name,
    u.email,
    u.phone,
    c.loyalty_points,
    COUNT(o.order_id) AS total_orders_placed,
    COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS successful_orders,
    COUNT(CASE WHEN o.order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
    COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE 0 END), 0.00) AS total_amount_spent,
    COALESCE(AVG(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE NULL END), 0.00) AS average_spend_per_order,
    MAX(o.placed_at) AS latest_order_date
FROM customers c
JOIN users u ON c.user_id = u.user_id
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, u.user_id, u.full_name, u.email, u.phone, c.loyalty_points;

