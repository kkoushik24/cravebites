-- =============================================================================
-- Dabba: Online Food Ordering System - Triggers & Stored Procedures (MySQL 8)
-- =============================================================================

USE dabba_db;

DROP TRIGGER IF EXISTS trg_reduce_stock_after_order;
DROP TRIGGER IF EXISTS trg_recalculate_order_total_insert;
DROP TRIGGER IF EXISTS trg_recalculate_order_total_update;
DROP TRIGGER IF EXISTS trg_recalculate_order_total_delete;
DROP TRIGGER IF EXISTS trg_order_status_audit;
DROP TRIGGER IF EXISTS trg_order_insert_audit;

DROP PROCEDURE IF EXISTS place_order;
DROP PROCEDURE IF EXISTS cancel_order;
DROP PROCEDURE IF EXISTS monthly_sales_report;

DELIMITER $$

-- -----------------------------------------------------------------------------
-- TRIGGER 1: Reduce stock & update availability when an order item is placed
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_reduce_stock_after_order
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE menu_items
    SET stock_quantity = GREATEST(0, stock_quantity - NEW.quantity),
        is_available = CASE WHEN (stock_quantity - NEW.quantity) <= 0 THEN 0 ELSE is_available END
    WHERE item_id = NEW.item_id;
END$$

-- -----------------------------------------------------------------------------
-- TRIGGER 2: Recalculate order subtotal, tax (5% GST), and total on item insert
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_recalculate_order_total_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_subtotal DECIMAL(10, 2);
    DECLARE v_tax DECIMAL(10, 2);
    DECLARE v_discount DECIMAL(10, 2);
    DECLARE v_delivery DECIMAL(10, 2);
    
    SELECT COALESCE(SUM(item_total), 0) INTO v_subtotal
    FROM order_items
    WHERE order_id = NEW.order_id;
    
    SELECT discount_amount, delivery_fee INTO v_discount, v_delivery
    FROM orders
    WHERE order_id = NEW.order_id;
    
    SET v_tax = ROUND(v_subtotal * 0.05, 2);
    
    UPDATE orders
    SET subtotal = v_subtotal,
        tax_amount = v_tax,
        total_amount = GREATEST(0.00, ROUND(v_subtotal - v_discount + v_delivery + v_tax, 2))
    WHERE order_id = NEW.order_id;
END$$

-- -----------------------------------------------------------------------------
-- TRIGGER 3: Recalculate order total on item update
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_recalculate_order_total_update
AFTER UPDATE ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_subtotal DECIMAL(10, 2);
    DECLARE v_tax DECIMAL(10, 2);
    DECLARE v_discount DECIMAL(10, 2);
    DECLARE v_delivery DECIMAL(10, 2);
    
    SELECT COALESCE(SUM(item_total), 0) INTO v_subtotal
    FROM order_items
    WHERE order_id = NEW.order_id;
    
    SELECT discount_amount, delivery_fee INTO v_discount, v_delivery
    FROM orders
    WHERE order_id = NEW.order_id;
    
    SET v_tax = ROUND(v_subtotal * 0.05, 2);
    
    UPDATE orders
    SET subtotal = v_subtotal,
        tax_amount = v_tax,
        total_amount = GREATEST(0.00, ROUND(v_subtotal - v_discount + v_delivery + v_tax, 2))
    WHERE order_id = NEW.order_id;
END$$

-- -----------------------------------------------------------------------------
-- TRIGGER 4: Recalculate order total on item delete
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_recalculate_order_total_delete
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_subtotal DECIMAL(10, 2);
    DECLARE v_tax DECIMAL(10, 2);
    DECLARE v_discount DECIMAL(10, 2);
    DECLARE v_delivery DECIMAL(10, 2);
    
    SELECT COALESCE(SUM(item_total), 0) INTO v_subtotal
    FROM order_items
    WHERE order_id = OLD.order_id;
    
    SELECT discount_amount, delivery_fee INTO v_discount, v_delivery
    FROM orders
    WHERE order_id = OLD.order_id;
    
    SET v_tax = ROUND(v_subtotal * 0.05, 2);
    
    UPDATE orders
    SET subtotal = v_subtotal,
        tax_amount = v_tax,
        total_amount = GREATEST(0.00, ROUND(v_subtotal - v_discount + v_delivery + v_tax, 2))
    WHERE order_id = OLD.order_id;
END$$

-- -----------------------------------------------------------------------------
-- TRIGGER 5: Log every order status change into audit_log
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_order_status_audit
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.order_status <> NEW.order_status THEN
        INSERT INTO audit_log (order_id, old_status, new_status, change_notes, created_at)
        VALUES (
            NEW.order_id,
            OLD.order_status,
            NEW.order_status,
            CONCAT('Order status transitioned from ', OLD.order_status, ' to ', NEW.order_status),
            NOW()
        );
    END IF;
END$$

-- -----------------------------------------------------------------------------
-- TRIGGER 6: Log initial order placement into audit_log
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_order_insert_audit
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (order_id, old_status, new_status, change_notes, created_at)
    VALUES (
        NEW.order_id,
        NULL,
        NEW.order_status,
        CONCAT('New order placed with status: ', NEW.order_status),
        NOW()
    );
END$$

-- -----------------------------------------------------------------------------
-- STORED PROCEDURE 1: place_order
-- Places an order with full TRANSACTION handling, rollback on failure,
-- stock validation, coupon calculation, item insertion, and partner auto-assign.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE place_order(
    IN p_customer_id INT,
    IN p_restaurant_id INT,
    IN p_address_id INT,
    IN p_coupon_code VARCHAR(30),
    IN p_payment_method VARCHAR(20),
    IN p_special_instructions TEXT,
    IN p_items_json JSON,
    OUT p_order_id INT,
    OUT p_status_message VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_restaurant_open TINYINT(1) DEFAULT 0;
    DECLARE v_customer_exists INT DEFAULT 0;
    DECLARE v_coupon_id INT DEFAULT NULL;
    DECLARE v_discount_pct DECIMAL(5, 2) DEFAULT 0.00;
    DECLARE v_flat_disc DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_max_disc DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_min_order DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_coupon_active TINYINT(1) DEFAULT 0;
    DECLARE v_coupon_valid DATETIME;
    DECLARE v_delivery_fee DECIMAL(10, 2) DEFAULT 40.00;
    DECLARE v_order_id INT;
    DECLARE v_partner_id INT DEFAULT NULL;
    DECLARE v_txn_ref VARCHAR(100);
    DECLARE v_computed_discount DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_est_minutes INT DEFAULT 30;
    DECLARE v_current_subtotal DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_item_count INT DEFAULT 0;
    DECLARE v_idx INT DEFAULT 0;
    DECLARE v_cur_item_id INT;
    DECLARE v_cur_qty INT;
    DECLARE v_cur_name VARCHAR(120);
    DECLARE v_cur_price DECIMAL(10, 2);
    DECLARE v_cur_stock INT DEFAULT 0;

    -- Error handler: Rollback on any SQL exception
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_order_id = NULL;
        SET p_status_message = 'Transaction aborted: A database error occurred during order processing.';
    END;

    START TRANSACTION;

    -- 1. Validate Customer
    SELECT COUNT(*) INTO v_customer_exists FROM customers WHERE customer_id = p_customer_id;
    IF v_customer_exists = 0 THEN
        ROLLBACK;
        SET p_order_id = NULL;
        SET p_status_message = 'Error: Invalid customer account.';
        LEAVE proc_block;
    END IF;

    -- 2. Validate Restaurant
    SELECT is_accepting_orders, prep_time_min + 15 INTO v_restaurant_open, v_est_minutes
    FROM restaurants WHERE restaurant_id = p_restaurant_id;
    
    IF v_restaurant_open IS NULL OR v_restaurant_open = 0 THEN
        ROLLBACK;
        SET p_order_id = NULL;
        SET p_status_message = 'Error: Restaurant is currently not accepting orders.';
        LEAVE proc_block;
    END IF;

    -- 3. Check Coupon if provided
    IF p_coupon_code IS NOT NULL AND TRIM(p_coupon_code) <> '' THEN
        SELECT coupon_id, discount_percentage, flat_discount, max_discount, min_order_amount, is_active, valid_until
        INTO v_coupon_id, v_discount_pct, v_flat_disc, v_max_disc, v_min_order, v_coupon_active, v_coupon_valid
        FROM coupons WHERE code = TRIM(p_coupon_code) LIMIT 1;

        IF v_coupon_id IS NOT NULL AND v_coupon_active = 1 AND v_coupon_valid >= NOW() THEN
            -- Coupon will be applied based on items total
            SET v_computed_discount = 0.00; -- Will calculate after subtotal
        ELSE
            SET v_coupon_id = NULL;
        END IF;
    END IF;

    -- 4. Insert Initial Order record (subtotal and total calculated via items trigger)
    INSERT INTO orders (
        customer_id, restaurant_id, address_id, coupon_id,
        order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount,
        special_instructions, estimated_delivery_minutes, placed_at
    ) VALUES (
        p_customer_id, p_restaurant_id, p_address_id, v_coupon_id,
        'Placed', 0.00, 0.00, v_delivery_fee, 0.00, v_delivery_fee,
        p_special_instructions, v_est_minutes, NOW()
    );

    SET v_order_id = LAST_INSERT_ID();

    -- 5. Insert Order Items from JSON Array in a loop
    -- (Uses FOR UPDATE row locking to strictly prevent overselling stock)
    SET v_item_count = JSON_LENGTH(p_items_json);
    SET v_idx = 0;

    WHILE v_idx < v_item_count DO
        SET v_cur_item_id = CAST(JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_idx, '].item_id'))) AS UNSIGNED);
        SET v_cur_qty = CAST(JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_idx, '].quantity'))) AS UNSIGNED);
        SET v_cur_name = NULL;
        SET v_cur_price = 0.00;
        SET v_cur_stock = 0;

        SELECT name, price, stock_quantity INTO v_cur_name, v_cur_price, v_cur_stock
        FROM menu_items
        WHERE item_id = v_cur_item_id AND restaurant_id = p_restaurant_id AND is_available = 1
        LIMIT 1
        FOR UPDATE;

        IF v_cur_name IS NULL THEN
            ROLLBACK;
            SET p_order_id = NULL;
            SET p_status_message = 'Error: One or more selected dishes are currently unavailable.';
            LEAVE proc_block;
        END IF;

        IF v_cur_stock < v_cur_qty THEN
            ROLLBACK;
            SET p_order_id = NULL;
            SET p_status_message = CONCAT('Error: Insufficient stock for ', v_cur_name, '. Only ', v_cur_stock, ' left.');
            LEAVE proc_block;
        END IF;

        IF v_cur_qty > 0 THEN
            INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, item_total)
            VALUES (v_order_id, v_cur_item_id, v_cur_name, v_cur_price, v_cur_qty, ROUND(v_cur_price * v_cur_qty, 2));
        END IF;

        SET v_idx = v_idx + 1;
    END WHILE;

    -- 6. Apply Coupon Discount if applicable based on subtotal
    IF v_coupon_id IS NOT NULL THEN
        SELECT subtotal INTO v_current_subtotal FROM orders WHERE order_id = v_order_id;
        
        IF v_current_subtotal >= v_min_order THEN
            IF v_discount_pct > 0 THEN
                SET v_computed_discount = LEAST(v_max_disc, ROUND(v_current_subtotal * (v_discount_pct / 100.0), 2));
            ELSEIF v_flat_disc > 0 THEN
                SET v_computed_discount = LEAST(v_max_disc, v_flat_disc);
            END IF;
            
            UPDATE orders
            SET discount_amount = v_computed_discount,
                total_amount = GREATEST(0.00, ROUND(subtotal - v_computed_discount + delivery_fee + tax_amount, 2))
            WHERE order_id = v_order_id;
        END IF;
    END IF;

    -- 7. Record Payment
    SET v_txn_ref = CONCAT('TXN-', UNIX_TIMESTAMP(), '-', FLOOR(1000 + RAND() * 9000));
    INSERT INTO payments (
        order_id, payment_method, payment_status, transaction_reference, amount, paid_at
    )
    SELECT 
        v_order_id,
        CASE WHEN LOWER(p_payment_method) = 'cod' THEN 'cod' ELSE 'online' END,
        'Completed',
        v_txn_ref,
        total_amount,
        NOW()
    FROM orders WHERE order_id = v_order_id;

    -- 8. Delivery partner is not assigned immediately.
    -- The restaurant will send a pickup request to nearby delivery partner when preparing food.
    COMMIT;

    SET p_order_id = v_order_id;
    SET p_status_message = 'Order placed successfully!';
END$$

-- -----------------------------------------------------------------------------
-- STORED PROCEDURE 2: cancel_order
-- Cancels an order with status validation, stock restoration, refund record,
-- delivery partner release, and audit trail update.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE cancel_order(
    IN p_order_id INT,
    IN p_user_id INT,
    IN p_reason VARCHAR(255),
    OUT p_success TINYINT(1),
    OUT p_message VARCHAR(255)
)
proc_cancel: BEGIN
    DECLARE v_current_status VARCHAR(40);
    DECLARE v_partner_id INT DEFAULT NULL;
    DECLARE v_pay_method VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Cancellation failed due to a database error.';
    END;

    START TRANSACTION;

    SELECT order_status, delivery_partner_id INTO v_current_status, v_partner_id
    FROM orders
    WHERE order_id = p_order_id;

    IF v_current_status IS NULL THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = 'Error: Order does not exist.';
        LEAVE proc_cancel;
    END IF;

    IF v_current_status NOT IN ('Placed', 'Accepted') THEN
        ROLLBACK;
        SET p_success = 0;
        SET p_message = CONCAT('Cannot cancel order: current status is already ', v_current_status);
        LEAVE proc_cancel;
    END IF;

    -- 1. Update order status to Cancelled
    UPDATE orders
    SET order_status = 'Cancelled',
        cancelled_at = NOW()
    WHERE order_id = p_order_id;

    -- 2. Restore menu item stock
    UPDATE menu_items m
    JOIN order_items oi ON m.item_id = oi.item_id
    SET m.stock_quantity = m.stock_quantity + oi.quantity,
        m.is_available = 1
    WHERE oi.order_id = p_order_id;

    -- 3. Update payment status to Refunded
    SELECT payment_method INTO v_pay_method FROM payments WHERE order_id = p_order_id LIMIT 1;
    IF v_pay_method = 'online' THEN
        UPDATE payments
        SET payment_status = 'Refunded'
        WHERE order_id = p_order_id;
    END IF;

    -- 4. Free delivery partner if one was assigned
    IF v_partner_id IS NOT NULL THEN
        UPDATE delivery_partners
        SET current_status = 'available'
        WHERE partner_id = v_partner_id;

        UPDATE deliveries
        SET status = 'cancelled'
        WHERE order_id = p_order_id;
    END IF;

    -- 5. Add audit log note
    INSERT INTO audit_log (order_id, old_status, new_status, changed_by_user_id, change_notes, created_at)
    VALUES (
        p_order_id,
        v_current_status,
        'Cancelled',
        p_user_id,
        CONCAT('Order cancelled. Reason: ', COALESCE(p_reason, 'User requested cancellation')),
        NOW()
    );

    COMMIT;

    SET p_success = 1;
    SET p_message = 'Order successfully cancelled and inventory restored.';
END$$

-- -----------------------------------------------------------------------------
-- STORED PROCEDURE 3: monthly_sales_report
-- Generates a consolidated sales report for a restaurant by year and month.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE monthly_sales_report(
    IN p_restaurant_id INT,
    IN p_year INT,
    IN p_month INT
)
BEGIN
    SELECT 
        r.restaurant_id,
        r.name AS restaurant_name,
        p_year AS report_year,
        p_month AS report_month,
        COUNT(o.order_id) AS total_orders,
        COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN o.order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.subtotal ELSE 0 END), 0.00) AS gross_merchandise_value,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.discount_amount ELSE 0 END), 0.00) AS total_discounts_offered,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.tax_amount ELSE 0 END), 0.00) AS total_tax_collected,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE 0 END), 0.00) AS net_revenue,
        COALESCE(AVG(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE NULL END), 0.00) AS avg_order_value
    FROM restaurants r
    LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
        AND YEAR(o.placed_at) = p_year
        AND MONTH(o.placed_at) = p_month
    WHERE r.restaurant_id = p_restaurant_id
    GROUP BY r.restaurant_id, r.name;
END$$

DELIMITER ;
