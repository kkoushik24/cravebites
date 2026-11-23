-- =============================================================================
-- Dabba: Online Food Ordering System - Demonstration SQL Queries
-- Demonstrates:
-- 1. Complex multi-table JOINs
-- 2. Subqueries (Correlated & Non-correlated)
-- 3. Aggregations with GROUP BY and HAVING
-- 4. Window Function: RANK() of restaurants by revenue
-- 5. Window Function: DENSE_RANK() of menu items by price within categories
-- =============================================================================

USE dabba_db;

-- -----------------------------------------------------------------------------
-- QUERY 1: Complex Multi-Table JOIN
-- Concept Demonstrated: 5-table INNER/LEFT JOIN connecting Orders, Customers,
-- Users, Restaurants, Delivery Partners, and Payments to generate an end-to-end
-- delivery fulfillment summary.
-- -----------------------------------------------------------------------------
SELECT 
    o.order_id,
    o.placed_at,
    u_cust.full_name AS customer_name,
    u_cust.phone AS customer_phone,
    r.name AS restaurant_name,
    r.cuisine_type,
    o.order_status,
    p.payment_method,
    p.payment_status,
    o.total_amount,
    COALESCE(u_part.full_name, 'Unassigned') AS delivery_partner_name,
    COALESCE(dp.vehicle_type, 'N/A') AS partner_vehicle
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN users u_cust ON c.user_id = u_cust.user_id
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN delivery_partners dp ON o.delivery_partner_id = dp.partner_id
LEFT JOIN users u_part ON dp.user_id = u_part.user_id
JOIN payments p ON o.order_id = p.order_id
ORDER BY o.placed_at DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- QUERY 2: Correlated Subquery
-- Concept Demonstrated: Correlated subquery in the WHERE clause to find menu items
-- whose price is higher than the average price of dishes within their OWN restaurant.
-- -----------------------------------------------------------------------------
SELECT 
    m.item_id,
    m.name AS premium_dish,
    r.name AS restaurant_name,
    m.price,
    ROUND((
        SELECT AVG(m2.price) 
        FROM menu_items m2 
        WHERE m2.restaurant_id = m.restaurant_id
    ), 2) AS restaurant_avg_dish_price,
    ROUND(m.price - (
        SELECT AVG(m2.price) 
        FROM menu_items m2 
        WHERE m2.restaurant_id = m.restaurant_id
    ), 2) AS premium_difference
FROM menu_items m
JOIN restaurants r ON m.restaurant_id = r.restaurant_id
WHERE m.price > (
    SELECT AVG(m2.price)
    FROM menu_items m2
    WHERE m2.restaurant_id = m.restaurant_id
)
ORDER BY r.name ASC, m.price DESC;


-- -----------------------------------------------------------------------------
-- QUERY 3: Non-Correlated Subquery with IN
-- Concept Demonstrated: Subquery returning a scalar list to find customers who have
-- placed at least one order that used a discount coupon and had total spend > ₹400.
-- -----------------------------------------------------------------------------
SELECT 
    c.customer_id,
    u.full_name,
    u.email,
    u.phone,
    c.loyalty_points
FROM customers c
JOIN users u ON c.user_id = u.user_id
WHERE c.customer_id IN (
    SELECT DISTINCT o.customer_id
    FROM orders o
    WHERE o.coupon_id IS NOT NULL 
      AND o.total_amount >= 400.00
      AND o.order_status = 'Delivered'
)
ORDER BY c.loyalty_points DESC;


-- -----------------------------------------------------------------------------
-- QUERY 4: Aggregation with GROUP BY and HAVING
-- Concept Demonstrated: Aggregating restaurant order metrics and using the HAVING
-- clause to filter only high-performing restaurants that have fulfilled at least
-- 3 delivered orders and generated over ₹1,000 in gross sales.
-- -----------------------------------------------------------------------------
SELECT 
    r.restaurant_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    COUNT(o.order_id) AS total_orders,
    COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS successful_deliveries,
    ROUND(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE 0 END), 2) AS total_revenue,
    ROUND(AVG(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE NULL END), 2) AS avg_ticket_size
FROM restaurants r
JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.name, r.cuisine_type
HAVING successful_deliveries >= 3 
   AND total_revenue > 1000.00
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- QUERY 5: Window Function - RANK() of Restaurants by Net Revenue
-- Concept Demonstrated: SQL Analytic Window Function RANK() to dynamically rank
-- restaurants based on their total delivered revenue without losing row-level details.
-- -----------------------------------------------------------------------------
SELECT 
    r.restaurant_id,
    r.name AS restaurant_name,
    r.cuisine_type,
    r.rating,
    COUNT(o.order_id) AS delivered_orders,
    COALESCE(SUM(o.total_amount), 0.00) AS net_revenue,
    RANK() OVER (ORDER BY COALESCE(SUM(o.total_amount), 0.00) DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY r.rating DESC) AS rating_rank
FROM restaurants r
LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id AND o.order_status = 'Delivered'
GROUP BY r.restaurant_id, r.name, r.cuisine_type, r.rating
ORDER BY revenue_rank ASC;


-- -----------------------------------------------------------------------------
-- QUERY 6: Window Function - DENSE_RANK() of Menu Items Partitioned by Category
-- Concept Demonstrated: DENSE_RANK() with PARTITION BY to determine the price
-- tier of each dish relative to other dishes within the same category.
-- -----------------------------------------------------------------------------
SELECT 
    c.name AS category,
    m.name AS dish_name,
    r.name AS restaurant,
    m.is_veg,
    m.price,
    DENSE_RANK() OVER (
        PARTITION BY c.category_id 
        ORDER BY m.price ASC
    ) AS price_tier_within_category
FROM menu_items m
JOIN categories c ON m.category_id = c.category_id
JOIN restaurants r ON m.restaurant_id = r.restaurant_id
ORDER BY c.display_order ASC, price_tier_within_category ASC;

