-- =============================================================================
-- Dabba: Online Food Ordering System - Realistic Seed Data
-- Comprehensive sample data: 3 roles, 5 restaurants, 45+ dishes, 10 customers,
-- 5 delivery partners, 30+ orders, coupons, reviews, and audit logs.
-- All demo user passwords are: password123
-- =============================================================================

USE dabba_db;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE audit_log;
TRUNCATE TABLE reviews;
TRUNCATE TABLE deliveries;
TRUNCATE TABLE delivery_partners;
TRUNCATE TABLE payments;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
TRUNCATE TABLE coupons;
TRUNCATE TABLE menu_items;
TRUNCATE TABLE categories;
TRUNCATE TABLE restaurants;
TRUNCATE TABLE addresses;
TRUNCATE TABLE customers;
TRUNCATE TABLE users;
TRUNCATE TABLE roles;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- 1. ROLES
-- -----------------------------------------------------------------------------
INSERT INTO roles (role_id, role_name, description) VALUES
(1, 'customer', 'Customer who browses restaurants, carts dishes, and places orders'),
(2, 'restaurant', 'Restaurant kitchen manager handling incoming orders and menu items'),
(3, 'delivery_partner', 'Delivery agent managing order pickups and door-step drops');

-- Common password hash for 'password123':
-- scrypt:32768:8:1$CRcTxKozt9jbwAmk$8061825b535c85420c978f3db3cef87e99bf5dfd294bac82656c42f5bf74ffb4741b35995dff2d97580614bd3a6177c8d539f143b91548a0109b802b0dc85347
SET @DEFAULT_HASH = 'scrypt:32768:8:1$CRcTxKozt9jbwAmk$8061825b535c85420c978f3db3cef87e99bf5dfd294bac82656c42f5bf74ffb4741b35995dff2d97580614bd3a6177c8d539f143b91548a0109b802b0dc85347';

-- -----------------------------------------------------------------------------
-- 2. USERS
-- -----------------------------------------------------------------------------
-- Demo Accounts:
-- Customer: customer@dabba.com
-- Restaurant: restaurant@dabba.com (Ember & Rice)
-- Delivery: delivery@dabba.com (Ravi Kumar)
INSERT INTO users (user_id, role_id, full_name, email, phone, password_hash) VALUES
-- Customers (1 - 10)
(1, 1, 'Aarav Sharma', 'customer@dabba.com', '9876543210', @DEFAULT_HASH),
(2, 1, 'Ananya Iyer', 'ananya@dabba.com', '9876543211', @DEFAULT_HASH),
(3, 1, 'Rohan Verma', 'rohan@dabba.com', '9876543212', @DEFAULT_HASH),
(4, 1, 'Pooja Hegde', 'pooja@dabba.com', '9876543213', @DEFAULT_HASH),
(5, 1, 'Karthik Rao', 'karthik@dabba.com', '9876543214', @DEFAULT_HASH),
(6, 1, 'Sneha Menon', 'sneha@dabba.com', '9876543215', @DEFAULT_HASH),
(7, 1, 'Vikram Deshmukh', 'vikram.d@dabba.com', '9876543216', @DEFAULT_HASH),
(8, 1, 'Neha Gupta', 'neha@dabba.com', '9876543217', @DEFAULT_HASH),
(9, 1, 'Aditya Joshi', 'aditya@dabba.com', '9876543218', @DEFAULT_HASH),
(10, 1, 'Meera Nair', 'meera@dabba.com', '9876543219', @DEFAULT_HASH),

-- Restaurants (11 - 15)
(11, 2, 'Ember & Rice Kitchen', 'restaurant@dabba.com', '9876543220', @DEFAULT_HASH),
(12, 2, 'Dosa Kingdom', 'dosa@dabba.com', '9876543221', @DEFAULT_HASH),
(13, 2, 'Delhi Zaika Express', 'delhi@dabba.com', '9876543222', @DEFAULT_HASH),
(14, 2, 'Mumbai Chaat & Thali', 'thali@dabba.com', '9876543223', @DEFAULT_HASH),
(15, 2, 'Royal Sweets & Desserts', 'sweets@dabba.com', '9876543224', @DEFAULT_HASH),

-- Delivery Partners (16 - 20)
(16, 3, 'Ravi Kumar', 'delivery@dabba.com', '9876543230', @DEFAULT_HASH),
(17, 3, 'Suresh Patel', 'suresh@dabba.com', '9876543231', @DEFAULT_HASH),
(18, 3, 'Amit Singh', 'amit@dabba.com', '9876543232', @DEFAULT_HASH),
(19, 3, 'Priya Nair', 'priya.n@dabba.com', '9876543233', @DEFAULT_HASH),
(20, 3, 'Vikram Reddy', 'vikram.r@dabba.com', '9876543234', @DEFAULT_HASH);

-- -----------------------------------------------------------------------------
-- 3. CUSTOMERS
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_id, user_id, loyalty_points) VALUES
(1, 1, 150),
(2, 2, 80),
(3, 3, 220),
(4, 4, 45),
(5, 5, 310),
(6, 6, 95),
(7, 7, 120),
(8, 8, 60),
(9, 9, 180),
(10, 10, 240);

-- -----------------------------------------------------------------------------
-- 4. ADDRESSES
-- -----------------------------------------------------------------------------
INSERT INTO addresses (address_id, customer_id, label, address_line, landmark, city, postal_code, latitude, longitude, is_default) VALUES
(1, 1, 'Home', 'Flat 402, Green Glen Layout, 4th Block, Koramangala', 'Near Sony Signal', 'Bengaluru', '560034', 12.9352, 77.6245, 1),
(2, 1, 'Work', '6th Floor, Enzyme Tech Park, HSR Layout Sector 6', 'Opposite Silk Board', 'Bengaluru', '560102', 12.9172, 77.6321, 0),
(3, 2, 'Home', 'House #12, 7th Main, Indiranagar', 'Behind Toit Pub', 'Bengaluru', '560038', 12.9784, 77.6408, 1),
(4, 3, 'Home', 'Villa 8, Palm Meadows, Whitefield', 'Near Forum Mall', 'Bengaluru', '560066', 12.9698, 77.7499, 1),
(5, 4, 'Home', 'Flat 204, Tower B, Lakeview Apartments, BTM 2nd Stage', 'Near Udupi Garden', 'Bengaluru', '560076', 12.9166, 77.6101, 1),
(6, 5, 'Home', 'B-303, Prestige Falcon City, Kanakapura Road', 'Near Metro Station', 'Bengaluru', '560062', 12.8912, 77.5684, 1),
(7, 6, 'Home', '55, 14th Cross, Malleshwaram', 'Near CTR Dosa Point', 'Bengaluru', '560003', 13.0031, 77.5643, 1),
(8, 7, 'Home', '101, Brigade Metropolis, Mahadevapura', 'Near Decathlon', 'Bengaluru', '560048', 12.9926, 77.7011, 1),
(9, 8, 'Home', '22, 1st Cross, Jayanagar 4th Block', 'Near Cool Joint', 'Bengaluru', '560011', 12.9299, 77.5824, 1),
(10, 9, 'Home', 'Flat 502, Sobha Forest View, Hosur Road', 'Opposite Electronic City Gate 1', 'Bengaluru', '560100', 12.8452, 77.6602, 1),
(11, 10, 'Home', '18, 3rd Stage, Basaveshwaranagar', 'Near Shankar Mutt', 'Bengaluru', '560079', 12.9881, 77.5382, 1);

-- -----------------------------------------------------------------------------
-- 5. RESTAURANTS
-- -----------------------------------------------------------------------------
INSERT INTO restaurants (restaurant_id, user_id, name, tagline, description, cuisine_type, rating, total_ratings, prep_time_min, is_accepting_orders, address, phone, accent_color) VALUES
(1, 11, 'Ember & Rice', 'Authentic Dum Biryanis & Charcoal Kebabs', 'Slow-cooked royal biryanis, succulent kebabs and aromatic Mughlai delicacies crafted with heritage spice blends.', 'Biryani, North Indian', 4.8, 385, 18, 1, 'Plot 88, 4th Block Market, Koramangala, Bengaluru', '080-41235678', '#2D1B4E'),
(2, 12, 'Dosa Kingdom', 'Crispy Ghee Dosas & South Indian Tiffins', 'Iconic South Indian culinary experience featuring butter-roasted dosas, fluffy idlis, and filter coffee.', 'South Indian', 4.7, 512, 12, 1, '14, 100 Feet Road, Indiranagar, Bengaluru', '080-41235679', '#176B3A'),
(3, 13, 'Delhi Zaika Express', 'Old Delhi Curries, Rolls & Tandoori', 'Taste of Chandni Chowk in Bengaluru: creamy butter chicken, crisp kathi rolls, and tandoori naans.', 'North Indian, Mughlai', 4.5, 290, 20, 1, '45, 80 Feet Road, 7th Block, Koramangala, Bengaluru', '080-41235680', '#A3162A'),
(4, 14, 'Mumbai Chaat & Thali', 'Street Treats & Grand Gujarati-Rajasthani Thalis', 'Wholesome royal thalis loaded with variety alongside tangy Mumbai sev puri, vada pav, and pav bhaji.', 'Thali, Street Food', 4.6, 340, 15, 1, '78, 27th Main, Sector 1, HSR Layout, Bengaluru', '080-41235681', '#B35C00'),
(5, 15, 'Royal Sweets & Desserts', 'Traditional Halwas, Phirni & Beverages', 'Rich dry-fruit halwas, chilled saffron phirni, artisanal rasmalai, and refreshing regional coolers.', 'Desserts, Beverages', 4.9, 195, 10, 1, '23, 11th Main, Jayanagar 4th Block, Bengaluru', '080-41235682', '#7A5A00');

-- -----------------------------------------------------------------------------
-- 6. CATEGORIES
-- -----------------------------------------------------------------------------
INSERT INTO categories (category_id, name, display_order) VALUES
(1, 'Biryani', 1),
(2, 'Dosa', 2),
(3, 'Thali', 3),
(4, 'Kebabs & Starters', 4),
(5, 'Curries & Breads', 5),
(6, 'Desserts', 6),
(7, 'Beverages', 7);

-- -----------------------------------------------------------------------------
-- 7. MENU_ITEMS (45+ realistic items across restaurants & categories)
-- -----------------------------------------------------------------------------
INSERT INTO menu_items (item_id, restaurant_id, category_id, name, description, price, is_veg, is_available, stock_quantity, image_letter, badge_bg, badge_text) VALUES
-- Ember & Rice (Items 1 - 12)
(1, 1, 1, 'Dum Biryani', 'Fragrant long-grain basmati cooked with caramelized onions, saffron, and tender spices.', 289.00, 1, 1, 35, 'B', '#FFEDBF', '#B35C00'),
(2, 1, 1, 'Chicken Dum Biryani', 'Hyderabadi style slow cooked biryani with marinated tender chicken pieces.', 319.00, 0, 1, 6, 'C', '#FFD6D6', '#A3162A'),
(3, 1, 1, 'Mutton Biryani', 'Succulent baby goat meat infused with Awadhi royal spices and aged basmati.', 399.00, 0, 1, 2, 'M', '#FFD9E8', '#9A1B55'),
(4, 1, 1, 'Veg Biryani', 'Garden-fresh vegetables and paneer layered with basmati and mint ghee.', 209.00, 1, 1, 25, 'V', '#D9EFE1', '#176B3A'),
(5, 1, 4, 'Seekh Kebab', 'Char-grilled minced meat rolls seasoned with fresh mint, coriander, and garam masala.', 220.00, 0, 1, 18, 'S', '#FFD9E8', '#9A1B55'),
(6, 1, 4, 'Paneer Tikka', 'Cottage cheese cubes tossed in spicy tandoori marinade and charred in clay oven.', 210.00, 1, 1, 22, 'P', '#FFEDBF', '#B35C00'),
(7, 1, 5, 'Butter Naan', 'Crisp and fluffy tandoori leavened flatbread brushed with golden butter.', 45.00, 1, 1, 50, 'N', '#FFF1B8', '#7A5A00'),
(8, 1, 5, 'Garlic Naan', 'Tandoor baked bread stuffed with minced garlic and cilantro butter.', 55.00, 1, 1, 40, 'G', '#FFF1B8', '#7A5A00'),
(9, 1, 5, 'Raita', 'Chilled creamy spiced curd with roasted cumin and finely chopped cucumbers.', 40.00, 1, 1, 45, 'R', '#D9EFE1', '#176B3A'),
(10, 1, 6, 'Phirni', 'Chilled Kashmiri rice pudding infused with saffron, cardamom, and sliced pistachios.', 80.00, 1, 0, 0, 'P', '#FFF1B8', '#7A5A00'),
(11, 1, 6, 'Gulab Jamun', 'Golden milk dumplings soaked in warm rosewater and saffron sugar syrup.', 60.00, 1, 1, 30, 'J', '#FFEDBF', '#B35C00'),
(12, 1, 7, 'Mango Lassi', 'Velvety sweet yogurt blend made with ripe Alphonso mango pulp.', 65.00, 1, 1, 28, 'L', '#FFEDBF', '#B35C00'),

-- Dosa Kingdom (Items 13 - 22)
(13, 2, 2, 'Masala Dosa', 'Golden crispy crepe stuffed with tempered spiced potato bhaji and served with chutneys.', 99.00, 1, 1, 60, 'D', '#D9EFE1', '#176B3A'),
(14, 2, 2, 'Ghee Roast Dosa', 'Ultra crisp dosa roasted with generous dollops of pure desi cow ghee.', 129.00, 1, 1, 50, 'G', '#FFEDBF', '#B35C00'),
(15, 2, 2, 'Mysore Masala Dosa', 'Crisp dosa smeared with spicy red garlic chili chutney and filled with potato mash.', 119.00, 1, 1, 45, 'M', '#FFD6D6', '#A3162A'),
(16, 2, 2, 'Onion Rava Dosa', 'Lacy semolina dosa studded with chopped onions, green chilies, and black pepper.', 109.00, 1, 1, 30, 'R', '#FFF1B8', '#7A5A00'),
(17, 2, 2, 'Cheese Dosa', 'Cheesy fusion dosa loaded with melted mozzarella and fresh herb seasoning.', 139.00, 1, 1, 25, 'C', '#FFEDBF', '#B35C00'),
(18, 2, 2, 'Set Dosa', 'Trio of sponge-soft, fluffy dosas served with creamy coconut chutney and sagu.', 89.00, 1, 1, 40, 'S', '#D9EFE1', '#176B3A'),
(19, 2, 5, 'Idli Vada Combo', 'Two steamed soft rice cakes and one crunchy medu vada with hot piping sambar.', 75.00, 1, 1, 50, 'I', '#FFF1B8', '#7A5A00'),
(20, 2, 5, 'Poori Sagu', 'Puffed deep-fried whole wheat breads served with traditional mixed vegetable sagu.', 85.00, 1, 1, 35, 'P', '#FFEDBF', '#B35C00'),
(21, 2, 7, 'Filter Coffee', 'Traditional South Indian chicory decoction brewed fresh with frothed full-cream milk.', 35.00, 1, 1, 80, 'F', '#FFD9E8', '#9A1B55'),
(22, 2, 7, 'Badam Milk', 'Warm almond milk flavored with saffron strands, crushed nuts, and green cardamom.', 50.00, 1, 1, 40, 'B', '#FFF1B8', '#7A5A00'),

-- Delhi Zaika Express (Items 23 - 31)
(23, 3, 4, 'Chicken Tikka Roll', 'Smoky chicken tikka rolled in flaky paratha with mint sauce and pickled red onions.', 179.00, 0, 1, 25, 'C', '#FFD6D6', '#A3162A'),
(24, 3, 4, 'Paneer Kathi Roll', 'Pan-roasted paneer batons with bell peppers wrapped in a crisp whole wheat rumali.', 149.00, 1, 1, 30, 'P', '#FFEDBF', '#B35C00'),
(25, 3, 5, 'Butter Chicken', 'Tandoor-pulled chicken in a rich, velvety tomato, butter, and cashew gravy.', 289.00, 0, 1, 20, 'B', '#FFD6D6', '#A3162A'),
(26, 3, 5, 'Dal Makhani', 'Overnight simmered black lentils and kidney beans finished with butter and cream.', 199.00, 1, 1, 35, 'D', '#1E1233', '#FFFFFF'),
(27, 3, 5, 'Kadhai Paneer', 'Fresh cottage cheese tossed with coarsely pounded coriander seeds and bell peppers.', 229.00, 1, 1, 28, 'K', '#FFEDBF', '#B35C00'),
(28, 3, 5, 'Tandoori Roti', 'Whole wheat unleavened flatbread freshly slapped onto clay oven walls.', 25.00, 1, 1, 70, 'T', '#FFF1B8', '#7A5A00'),
(29, 3, 4, 'Tandoori Chicken Full', 'Whole tender chicken marinated in Kashmiri chili yogurt and roasted to perfection.', 399.00, 0, 1, 15, 'T', '#FFD6D6', '#A3162A'),
(30, 3, 7, 'Sweet Lassi', 'Traditional Punjabi whipped yogurt drink topped with a thick layer of malai.', 55.00, 1, 1, 40, 'S', '#FFF1B8', '#7A5A00'),
(31, 3, 7, 'Masala Chai', 'Aromatic ginger-cardamom tea brewed with fresh milk.', 30.00, 1, 1, 60, 'M', '#FFEDBF', '#B35C00'),

-- Mumbai Chaat & Thali (Items 32 - 40)
(32, 4, 3, 'Veg Thali', 'Complete balance of paneer curry, dal tadka, 2 rotis, basmati rice, papad, and pickle.', 180.00, 1, 1, 40, 'T', '#FFD6D6', '#A3162A'),
(33, 4, 3, 'Special Rajasthani Thali', 'Dal baati churma, gatte ki sabzi, ker sangri, bajra roti, and chaas.', 249.00, 1, 1, 25, 'R', '#FFEDBF', '#B35C00'),
(34, 4, 3, 'Deluxe Maharaja Thali', 'Grand spread with 2 paneer dishes, dal makhani, pulao, 3 breads, sweet, and raita.', 320.00, 1, 1, 15, 'M', '#FFD9E8', '#9A1B55'),
(35, 4, 4, 'Pav Bhaji', 'Spiced buttery mashed vegetable curry served with toasted soft butter pav.', 130.00, 1, 1, 35, 'P', '#FFEDBF', '#B35C00'),
(36, 4, 4, 'Pani Puri (8 pcs)', 'Crisp semolina hollow puris filled with tangy spicy mint water and ragda.', 60.00, 1, 1, 50, 'P', '#D9EFE1', '#176B3A'),
(37, 4, 4, 'Sev Puri', 'Flat puris topped with boiled potatoes, raw onions, chutneys, and fine nylon sev.', 70.00, 1, 1, 45, 'S', '#FFEDBF', '#B35C00'),
(38, 4, 4, 'Dahi Puri', 'Crunchy puris stuffed with spiced potatoes, sweet yogurt, and tamarind chutney.', 80.00, 1, 1, 40, 'D', '#FFF1B8', '#7A5A00'),
(39, 4, 7, 'Masala Chaas', 'Refreshing churned spiced buttermilk garnished with fresh coriander and cumin.', 35.00, 1, 1, 50, 'C', '#D9EFE1', '#176B3A'),
(40, 4, 7, 'Kokum Sharbat', 'Coastal sweet and tangy cooler made from natural kokum extract.', 45.00, 1, 1, 30, 'K', '#FFD6D6', '#A3162A'),

-- Royal Sweets & Desserts (Items 41 - 47)
(41, 5, 6, 'Kesar Rasmalai (2 pcs)', 'Spongy cottage cheese patties immersed in chilled saffron infused clotted milk.', 90.00, 1, 1, 30, 'R', '#FFF1B8', '#7A5A00'),
(42, 5, 6, 'Gajar Ka Halwa (150g)', 'Slow-simmered winter carrots cooked with mawa, ghee, cashew, and golden raisins.', 85.00, 1, 1, 25, 'G', '#FFD6D6', '#A3162A'),
(43, 5, 6, 'Royal Saffron Phirni', 'Traditional ground rice slow-cooked in sweetened milk and garnished with edible silver foil.', 80.00, 1, 1, 30, 'P', '#FFF1B8', '#7A5A00'),
(44, 5, 6, 'Mango Kulfi on Stick', 'Creamy homemade Indian ice cream rich in pure Alphonso mango essence.', 70.00, 1, 1, 35, 'M', '#FFEDBF', '#B35C00'),
(45, 5, 6, 'Rabri with Jalebi', 'Crisp piping hot spiral jalebis served with thick reduced creamy cardamom rabri.', 95.00, 1, 1, 20, 'J', '#FFEDBF', '#B35C00'),
(46, 5, 7, 'Royal Thandai', 'Heritage festive milk beverage blended with almonds, fennel, melon seeds, and rose petals.', 75.00, 1, 1, 25, 'T', '#FFF1B8', '#7A5A00'),
(47, 5, 7, 'Fresh Lime Soda', 'Refreshing soda served with freshly squeezed lemon juice, mint, and black salt.', 50.00, 1, 1, 50, 'L', '#D9EFE1', '#176B3A');

-- -----------------------------------------------------------------------------
-- 8. COUPONS
-- -----------------------------------------------------------------------------
INSERT INTO coupons (coupon_id, code, discount_percentage, flat_discount, max_discount, min_order_amount, is_active, valid_until) VALUES
(1, 'DABBA50', 50.00, 0.00, 100.00, 200.00, 1, '2028-12-31 23:59:59'),
(2, 'FEAST100', 0.00, 100.00, 100.00, 400.00, 1, '2028-12-31 23:59:59'),
(3, 'WELCOME20', 20.00, 0.00, 60.00, 150.00, 1, '2028-12-31 23:59:59'),
(4, 'BIRYANI40', 40.00, 0.00, 80.00, 250.00, 1, '2028-12-31 23:59:59');

-- -----------------------------------------------------------------------------
-- 9. DELIVERY PARTNERS
-- -----------------------------------------------------------------------------
INSERT INTO delivery_partners (partner_id, user_id, vehicle_type, vehicle_number, is_online, current_status, current_lat, current_lng, total_trips, total_earnings, hours_online, rating) VALUES
(1, 16, 'Motorcycle', 'KA-01-AB-1234', 1, 'available', 12.9350, 77.6240, 14, 1240.00, 5.2, 4.8),
(2, 17, 'Scooter', 'KA-02-CD-5678', 1, 'available', 12.9780, 77.6400, 11, 980.00, 4.5, 4.7),
(3, 18, 'Motorcycle', 'KA-03-EF-9012', 1, 'available', 12.9170, 77.6320, 16, 1420.00, 6.0, 4.9),
(4, 19, 'Electric Bike', 'KA-04-GH-3456', 1, 'available', 12.9690, 77.7490, 9, 810.00, 3.8, 4.6),
(5, 20, 'Motorcycle', 'KA-05-IJ-7890', 0, 'offline', 12.8910, 77.5680, 8, 720.00, 3.2, 4.8);

-- -----------------------------------------------------------------------------
-- 10. HISTORICAL & LIVE ORDERS (30+ orders)
-- Order status flow: Placed -> Accepted -> Preparing -> Ready -> Picked up -> Delivered
-- Includes specific orders shown in design mockups (#2841, #2843, #2844, #2840, #2839)
-- -----------------------------------------------------------------------------

-- Live Order #2841 (Ready for pickup, partner assigned: Ravi Kumar, matching customer & restaurant UI)
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, special_instructions, estimated_delivery_minutes, placed_at, accepted_at, ready_at) VALUES
(2841, 1, 1, 1, 1, NULL, 'Ready', 359.00, 0.00, 40.00, 18.00, 417.00, 'Extra spicy raita please', 12, DATE_SUB(NOW(), INTERVAL 15 MINUTE), DATE_SUB(NOW(), INTERVAL 12 MINUTE), DATE_SUB(NOW(), INTERVAL 1 MINUTE));

-- Live Order #2843 (New / Placed)
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, special_instructions, estimated_delivery_minutes, placed_at) VALUES
(2843, 2, 1, NULL, 3, NULL, 'Placed', 399.00, 0.00, 40.00, 20.00, 459.00, 'Please send disposable cutlery', 25, DATE_SUB(NOW(), INTERVAL 2 MINUTE));

-- Live Order #2844 (New / Placed)
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, special_instructions, estimated_delivery_minutes, placed_at) VALUES
(2844, 3, 1, NULL, 4, NULL, 'Placed', 265.00, 0.00, 40.00, 13.00, 318.00, 'Do not ring bell, infant sleeping', 30, DATE_SUB(NOW(), INTERVAL 30 SECOND));

-- Live Order #2840 (Preparing)
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, special_instructions, estimated_delivery_minutes, placed_at, accepted_at) VALUES
(2840, 4, 1, 2, 5, NULL, 'Preparing', 627.00, 0.00, 40.00, 31.00, 698.00, 'Make it very mild', 18, DATE_SUB(NOW(), INTERVAL 10 MINUTE), DATE_SUB(NOW(), INTERVAL 8 MINUTE));

-- Live Order #2839 (Preparing)
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, special_instructions, estimated_delivery_minutes, placed_at, accepted_at) VALUES
(2839, 5, 1, 3, 6, NULL, 'Preparing', 479.00, 0.00, 40.00, 24.00, 543.00, 'Keep phirni chilled', 15, DATE_SUB(NOW(), INTERVAL 14 MINUTE), DATE_SUB(NOW(), INTERVAL 11 MINUTE));

-- Additional 26 orders for historical performance, hourly charts, and top selling views:
INSERT INTO orders (order_id, customer_id, restaurant_id, delivery_partner_id, address_id, coupon_id, order_status, subtotal, discount_amount, delivery_fee, tax_amount, total_amount, placed_at, accepted_at, ready_at, picked_at, delivered_at) VALUES
(2801, 1, 1, 1, 1, 1, 'Delivered', 498.00, 100.00, 40.00, 20.00, 458.00, DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_SUB(NOW(), INTERVAL 350 MINUTE), DATE_SUB(NOW(), INTERVAL 335 MINUTE), DATE_SUB(NOW(), INTERVAL 330 MINUTE), DATE_SUB(NOW(), INTERVAL 310 MINUTE)),
(2802, 2, 2, 2, 3, 3, 'Delivered', 228.00, 45.60, 40.00, 9.12, 231.52, DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_SUB(NOW(), INTERVAL 290 MINUTE), DATE_SUB(NOW(), INTERVAL 280 MINUTE), DATE_SUB(NOW(), INTERVAL 275 MINUTE), DATE_SUB(NOW(), INTERVAL 255 MINUTE)),
(2803, 3, 3, 3, 4, NULL, 'Delivered', 328.00, 0.00, 40.00, 16.40, 384.40, DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_SUB(NOW(), INTERVAL 285 MINUTE), DATE_SUB(NOW(), INTERVAL 265 MINUTE), DATE_SUB(NOW(), INTERVAL 260 MINUTE), DATE_SUB(NOW(), INTERVAL 240 MINUTE)),
(2804, 4, 4, 1, 5, 2, 'Delivered', 430.00, 100.00, 40.00, 16.50, 386.50, DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 230 MINUTE), DATE_SUB(NOW(), INTERVAL 215 MINUTE), DATE_SUB(NOW(), INTERVAL 210 MINUTE), DATE_SUB(NOW(), INTERVAL 190 MINUTE)),
(2805, 5, 5, 4, 6, NULL, 'Delivered', 245.00, 0.00, 40.00, 12.25, 297.25, DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 225 MINUTE), DATE_SUB(NOW(), INTERVAL 215 MINUTE), DATE_SUB(NOW(), INTERVAL 210 MINUTE), DATE_SUB(NOW(), INTERVAL 195 MINUTE)),
(2806, 6, 1, 2, 7, 1, 'Delivered', 608.00, 100.00, 40.00, 25.40, 573.40, DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_SUB(NOW(), INTERVAL 220 MINUTE), DATE_SUB(NOW(), INTERVAL 200 MINUTE), DATE_SUB(NOW(), INTERVAL 195 MINUTE), DATE_SUB(NOW(), INTERVAL 175 MINUTE)),
(2807, 7, 2, 3, 8, NULL, 'Delivered', 188.00, 0.00, 40.00, 9.40, 237.40, DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_SUB(NOW(), INTERVAL 170 MINUTE), DATE_SUB(NOW(), INTERVAL 160 MINUTE), DATE_SUB(NOW(), INTERVAL 155 MINUTE), DATE_SUB(NOW(), INTERVAL 140 MINUTE)),
(2808, 8, 3, 4, 9, 3, 'Delivered', 488.00, 60.00, 40.00, 21.40, 489.40, DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_SUB(NOW(), INTERVAL 165 MINUTE), DATE_SUB(NOW(), INTERVAL 145 MINUTE), DATE_SUB(NOW(), INTERVAL 140 MINUTE), DATE_SUB(NOW(), INTERVAL 120 MINUTE)),
(2809, 9, 4, 1, 10, NULL, 'Delivered', 250.00, 0.00, 40.00, 12.50, 302.50, DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_SUB(NOW(), INTERVAL 160 MINUTE), DATE_SUB(NOW(), INTERVAL 145 MINUTE), DATE_SUB(NOW(), INTERVAL 140 MINUTE), DATE_SUB(NOW(), INTERVAL 125 MINUTE)),
(2810, 10, 5, 2, 11, NULL, 'Delivered', 170.00, 0.00, 40.00, 8.50, 218.50, DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 115 MINUTE), DATE_SUB(NOW(), INTERVAL 105 MINUTE), DATE_SUB(NOW(), INTERVAL 100 MINUTE), DATE_SUB(NOW(), INTERVAL 85 MINUTE)),
(2811, 1, 1, 3, 1, 4, 'Delivered', 598.00, 80.00, 40.00, 25.90, 583.90, DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 110 MINUTE), DATE_SUB(NOW(), INTERVAL 95 MINUTE), DATE_SUB(NOW(), INTERVAL 90 MINUTE), DATE_SUB(NOW(), INTERVAL 70 MINUTE)),
(2812, 2, 2, 4, 3, NULL, 'Delivered', 327.00, 0.00, 40.00, 16.35, 383.35, DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 105 MINUTE), DATE_SUB(NOW(), INTERVAL 95 MINUTE), DATE_SUB(NOW(), INTERVAL 90 MINUTE), DATE_SUB(NOW(), INTERVAL 75 MINUTE)),
(2813, 3, 3, 1, 4, 1, 'Delivered', 374.00, 100.00, 40.00, 13.70, 327.70, DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_SUB(NOW(), INTERVAL 55 MINUTE), DATE_SUB(NOW(), INTERVAL 40 MINUTE), DATE_SUB(NOW(), INTERVAL 35 MINUTE), DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
(2814, 4, 1, 2, 5, NULL, 'Delivered', 329.00, 0.00, 40.00, 16.45, 385.45, DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_SUB(NOW(), INTERVAL 50 MINUTE), DATE_SUB(NOW(), INTERVAL 35 MINUTE), DATE_SUB(NOW(), INTERVAL 30 MINUTE), DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(2815, 5, 2, 3, 6, 3, 'Delivered', 218.00, 43.60, 40.00, 8.72, 223.12, DATE_SUB(NOW(), INTERVAL 45 MINUTE), DATE_SUB(NOW(), INTERVAL 40 MINUTE), DATE_SUB(NOW(), INTERVAL 30 MINUTE), DATE_SUB(NOW(), INTERVAL 25 MINUTE), DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
(2816, 6, 4, 4, 7, NULL, 'Delivered', 190.00, 0.00, 40.00, 9.50, 239.50, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 47 HOUR), DATE_SUB(NOW(), INTERVAL 46 HOUR), DATE_SUB(NOW(), INTERVAL 46 HOUR), DATE_SUB(NOW(), INTERVAL 45 HOUR)),
(2817, 7, 5, 1, 8, NULL, 'Delivered', 260.00, 0.00, 40.00, 13.00, 313.00, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 47 HOUR), DATE_SUB(NOW(), INTERVAL 46 HOUR), DATE_SUB(NOW(), INTERVAL 46 HOUR), DATE_SUB(NOW(), INTERVAL 45 HOUR)),
(2818, 8, 1, 2, 9, 2, 'Delivered', 718.00, 100.00, 40.00, 30.90, 688.90, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 71 HOUR), DATE_SUB(NOW(), INTERVAL 70 HOUR), DATE_SUB(NOW(), INTERVAL 70 HOUR), DATE_SUB(NOW(), INTERVAL 69 HOUR)),
(2819, 9, 3, 3, 10, NULL, 'Delivered', 418.00, 0.00, 40.00, 20.90, 478.90, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 71 HOUR), DATE_SUB(NOW(), INTERVAL 70 HOUR), DATE_SUB(NOW(), INTERVAL 70 HOUR), DATE_SUB(NOW(), INTERVAL 69 HOUR)),
(2820, 10, 2, 4, 11, NULL, 'Delivered', 298.00, 0.00, 40.00, 14.90, 352.90, DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 95 HOUR), DATE_SUB(NOW(), INTERVAL 94 HOUR), DATE_SUB(NOW(), INTERVAL 94 HOUR), DATE_SUB(NOW(), INTERVAL 93 HOUR)),
(2821, 1, 4, 1, 1, 1, 'Delivered', 500.00, 100.00, 40.00, 20.00, 460.00, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 119 HOUR), DATE_SUB(NOW(), INTERVAL 118 HOUR), DATE_SUB(NOW(), INTERVAL 118 HOUR), DATE_SUB(NOW(), INTERVAL 117 HOUR)),
(2822, 2, 5, 2, 3, NULL, 'Delivered', 315.00, 0.00, 40.00, 15.75, 370.75, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 119 HOUR), DATE_SUB(NOW(), INTERVAL 118 HOUR), DATE_SUB(NOW(), INTERVAL 118 HOUR), DATE_SUB(NOW(), INTERVAL 117 HOUR)),
(2823, 3, 1, 3, 4, NULL, 'Delivered', 399.00, 0.00, 40.00, 19.95, 458.95, DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 143 HOUR), DATE_SUB(NOW(), INTERVAL 142 HOUR), DATE_SUB(NOW(), INTERVAL 142 HOUR), DATE_SUB(NOW(), INTERVAL 141 HOUR)),
(2824, 4, 3, 4, 5, NULL, 'Delivered', 289.00, 0.00, 40.00, 14.45, 343.45, DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 167 HOUR), DATE_SUB(NOW(), INTERVAL 166 HOUR), DATE_SUB(NOW(), INTERVAL 166 HOUR), DATE_SUB(NOW(), INTERVAL 165 HOUR)),
(2825, 5, 2, 1, 6, NULL, 'Cancelled', 198.00, 0.00, 40.00, 9.90, 247.90, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 23 HOUR), NULL, NULL, NULL),
(2826, 6, 1, 2, 7, NULL, 'Rejected', 319.00, 0.00, 40.00, 15.95, 374.95, DATE_SUB(NOW(), INTERVAL 1 DAY), NULL, NULL, NULL, NULL);

-- -----------------------------------------------------------------------------
-- 11. ORDER_ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, item_total) VALUES
-- Order 2841 (Ready)
(2841, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00),
(2841, 9, 'Raita', 40.00, 1, 40.00),

-- Order 2843 (Placed)
(2843, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00),
(2843, 9, 'Raita', 40.00, 2, 80.00),

-- Order 2844 (Placed)
(2844, 5, 'Seekh Kebab', 220.00, 1, 220.00),
(2844, 7, 'Butter Naan', 45.00, 1, 45.00),

-- Order 2840 (Preparing)
(2840, 4, 'Veg Biryani', 209.00, 3, 627.00),

-- Order 2839 (Preparing)
(2839, 3, 'Mutton Biryani', 399.00, 1, 399.00),
(2839, 10, 'Phirni', 80.00, 1, 80.00),

-- Historical items:
(2801, 1, 'Dum Biryani', 289.00, 1, 289.00),
(2801, 6, 'Paneer Tikka', 209.00, 1, 209.00),
(2802, 13, 'Masala Dosa', 99.00, 1, 99.00),
(2802, 14, 'Ghee Roast Dosa', 129.00, 1, 129.00),
(2803, 23, 'Chicken Tikka Roll', 179.00, 1, 179.00),
(2803, 24, 'Paneer Kathi Roll', 149.00, 1, 149.00),
(2804, 32, 'Veg Thali', 180.00, 1, 180.00),
(2804, 33, 'Special Rajasthani Thali', 250.00, 1, 250.00),
(2805, 41, 'Kesar Rasmalai (2 pcs)', 90.00, 1, 90.00),
(2805, 42, 'Gajar Ka Halwa (150g)', 85.00, 1, 85.00),
(2805, 43, 'Royal Saffron Phirni', 70.00, 1, 70.00),
(2806, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00),
(2806, 1, 'Dum Biryani', 289.00, 1, 289.00),
(2807, 15, 'Mysore Masala Dosa', 119.00, 1, 119.00),
(2807, 21, 'Filter Coffee', 35.00, 1, 35.00),
(2807, 21, 'Filter Coffee', 34.00, 1, 34.00),
(2808, 25, 'Butter Chicken', 289.00, 1, 289.00),
(2808, 26, 'Dal Makhani', 199.00, 1, 199.00),
(2809, 35, 'Pav Bhaji', 130.00, 1, 130.00),
(2809, 36, 'Pani Puri (8 pcs)', 60.00, 2, 120.00),
(2810, 44, 'Mango Kulfi on Stick', 70.00, 1, 70.00),
(2810, 45, 'Rabri with Jalebi', 100.00, 1, 100.00),
(2811, 3, 'Mutton Biryani', 399.00, 1, 399.00),
(2811, 26, 'Dal Makhani', 199.00, 1, 199.00),
(2812, 17, 'Cheese Dosa', 139.00, 1, 139.00),
(2812, 18, 'Set Dosa', 89.00, 1, 89.00),
(2812, 14, 'Ghee Roast Dosa', 99.00, 1, 99.00),
(2813, 27, 'Kadhai Paneer', 229.00, 1, 229.00),
(2813, 24, 'Paneer Kathi Roll', 145.00, 1, 145.00),
(2814, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00),
(2814, 9, 'Raita', 10.00, 1, 10.00),
(2815, 13, 'Masala Dosa', 99.00, 1, 99.00),
(2815, 15, 'Mysore Masala Dosa', 119.00, 1, 119.00),
(2816, 32, 'Veg Thali', 180.00, 1, 180.00),
(2816, 39, 'Masala Chaas', 10.00, 1, 10.00),
(2817, 41, 'Kesar Rasmalai (2 pcs)', 90.00, 2, 180.00),
(2817, 43, 'Royal Saffron Phirni', 80.00, 1, 80.00),
(2818, 3, 'Mutton Biryani', 399.00, 1, 399.00),
(2818, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00),
(2819, 25, 'Butter Chicken', 289.00, 1, 289.00),
(2819, 35, 'Pav Bhaji', 129.00, 1, 129.00),
(2820, 14, 'Ghee Roast Dosa', 129.00, 2, 258.00),
(2820, 21, 'Filter Coffee', 40.00, 1, 40.00),
(2821, 34, 'Deluxe Maharaja Thali', 320.00, 1, 320.00),
(2821, 32, 'Veg Thali', 180.00, 1, 180.00),
(2822, 45, 'Rabri with Jalebi', 95.00, 2, 190.00),
(2822, 46, 'Royal Thandai', 125.00, 1, 125.00),
(2823, 3, 'Mutton Biryani', 399.00, 1, 399.00),
(2824, 25, 'Butter Chicken', 289.00, 1, 289.00),
(2825, 13, 'Masala Dosa', 99.00, 2, 198.00),
(2826, 2, 'Chicken Dum Biryani', 319.00, 1, 319.00);

-- -----------------------------------------------------------------------------
-- 12. PAYMENTS
-- -----------------------------------------------------------------------------
INSERT INTO payments (payment_id, order_id, payment_method, payment_status, transaction_reference, amount, paid_at) VALUES
(1, 2841, 'online', 'Completed', 'TXN-2841-ONLINE-9821', 417.00, DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
(2, 2843, 'online', 'Completed', 'TXN-2843-ONLINE-1204', 459.00, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(3, 2844, 'cod', 'Pending', 'TXN-2844-COD-3391', 318.00, DATE_SUB(NOW(), INTERVAL 30 SECOND)),
(4, 2840, 'online', 'Completed', 'TXN-2840-ONLINE-4482', 698.00, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(5, 2839, 'online', 'Completed', 'TXN-2839-ONLINE-7719', 543.00, DATE_SUB(NOW(), INTERVAL 14 MINUTE)),
(6, 2801, 'online', 'Completed', 'TXN-2801-ONLINE-1001', 458.00, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
(7, 2802, 'online', 'Completed', 'TXN-2802-ONLINE-1002', 231.52, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(8, 2803, 'cod', 'Completed', 'TXN-2803-COD-1003', 384.40, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(9, 2804, 'online', 'Completed', 'TXN-2804-ONLINE-1004', 386.50, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(10, 2805, 'online', 'Completed', 'TXN-2805-ONLINE-1005', 297.25, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(11, 2806, 'online', 'Completed', 'TXN-2806-ONLINE-1006', 573.40, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(12, 2807, 'online', 'Completed', 'TXN-2807-ONLINE-1007', 237.40, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(13, 2808, 'online', 'Completed', 'TXN-2808-ONLINE-1008', 489.40, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(14, 2809, 'cod', 'Completed', 'TXN-2809-COD-1009', 302.50, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(15, 2810, 'online', 'Completed', 'TXN-2810-ONLINE-1010', 218.50, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(16, 2811, 'online', 'Completed', 'TXN-2811-ONLINE-1011', 583.90, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(17, 2812, 'online', 'Completed', 'TXN-2812-ONLINE-1012', 383.35, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(18, 2813, 'online', 'Completed', 'TXN-2813-ONLINE-1013', 327.70, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(19, 2814, 'online', 'Completed', 'TXN-2814-ONLINE-1014', 385.45, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(20, 2815, 'online', 'Completed', 'TXN-2815-ONLINE-1015', 223.12, DATE_SUB(NOW(), INTERVAL 45 MINUTE)),
(21, 2816, 'online', 'Completed', 'TXN-2816-ONLINE-1016', 239.50, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(22, 2817, 'online', 'Completed', 'TXN-2817-ONLINE-1017', 313.00, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(23, 2818, 'online', 'Completed', 'TXN-2818-ONLINE-1018', 688.90, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(24, 2819, 'cod', 'Completed', 'TXN-2819-COD-1019', 478.90, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(25, 2820, 'online', 'Completed', 'TXN-2820-ONLINE-1020', 352.90, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(26, 2821, 'online', 'Completed', 'TXN-2821-ONLINE-1021', 460.00, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(27, 2822, 'online', 'Completed', 'TXN-2822-ONLINE-1022', 370.75, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(28, 2823, 'online', 'Completed', 'TXN-2823-ONLINE-1023', 458.95, DATE_SUB(NOW(), INTERVAL 6 DAY)),
(29, 2824, 'online', 'Completed', 'TXN-2824-ONLINE-1024', 343.45, DATE_SUB(NOW(), INTERVAL 7 DAY)),
(30, 2825, 'online', 'Refunded', 'TXN-2825-ONLINE-REF', 247.90, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(31, 2826, 'online', 'Refunded', 'TXN-2826-ONLINE-REF', 374.95, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- -----------------------------------------------------------------------------
-- 13. DELIVERIES
-- -----------------------------------------------------------------------------
INSERT INTO deliveries (delivery_id, order_id, partner_id, pickup_time, delivery_time, distance_km, delivery_fee_earned, status, created_at) VALUES
(1, 2841, 1, NULL, NULL, 3.2, 68.00, 'assigned', DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
(2, 2840, 2, NULL, NULL, 2.8, 55.00, 'assigned', DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(3, 2839, 3, NULL, NULL, 4.1, 72.00, 'assigned', DATE_SUB(NOW(), INTERVAL 14 MINUTE)),
(4, 2801, 1, DATE_SUB(NOW(), INTERVAL 330 MINUTE), DATE_SUB(NOW(), INTERVAL 310 MINUTE), 3.5, 65.00, 'delivered', DATE_SUB(NOW(), INTERVAL 6 HOUR)),
(5, 2802, 2, DATE_SUB(NOW(), INTERVAL 275 MINUTE), DATE_SUB(NOW(), INTERVAL 255 MINUTE), 2.2, 50.00, 'delivered', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(6, 2803, 3, DATE_SUB(NOW(), INTERVAL 260 MINUTE), DATE_SUB(NOW(), INTERVAL 240 MINUTE), 4.0, 70.00, 'delivered', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(7, 2804, 1, DATE_SUB(NOW(), INTERVAL 210 MINUTE), DATE_SUB(NOW(), INTERVAL 190 MINUTE), 2.9, 55.00, 'delivered', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(8, 2805, 4, DATE_SUB(NOW(), INTERVAL 210 MINUTE), DATE_SUB(NOW(), INTERVAL 195 MINUTE), 3.1, 58.00, 'delivered', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(9, 2806, 2, DATE_SUB(NOW(), INTERVAL 195 MINUTE), DATE_SUB(NOW(), INTERVAL 175 MINUTE), 4.5, 80.00, 'delivered', DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(10, 2807, 3, DATE_SUB(NOW(), INTERVAL 155 MINUTE), DATE_SUB(NOW(), INTERVAL 140 MINUTE), 1.8, 45.00, 'delivered', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(11, 2808, 4, DATE_SUB(NOW(), INTERVAL 140 MINUTE), DATE_SUB(NOW(), INTERVAL 120 MINUTE), 3.4, 62.00, 'delivered', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(12, 2809, 1, DATE_SUB(NOW(), INTERVAL 140 MINUTE), DATE_SUB(NOW(), INTERVAL 125 MINUTE), 2.7, 52.00, 'delivered', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(13, 2810, 2, DATE_SUB(NOW(), INTERVAL 100 MINUTE), DATE_SUB(NOW(), INTERVAL 85 MINUTE), 2.0, 48.00, 'delivered', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(14, 2811, 3, DATE_SUB(NOW(), INTERVAL 90 MINUTE), DATE_SUB(NOW(), INTERVAL 70 MINUTE), 3.8, 68.00, 'delivered', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(15, 2812, 4, DATE_SUB(NOW(), INTERVAL 90 MINUTE), DATE_SUB(NOW(), INTERVAL 75 MINUTE), 2.5, 50.00, 'delivered', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(16, 2813, 1, DATE_SUB(NOW(), INTERVAL 35 MINUTE), DATE_SUB(NOW(), INTERVAL 15 MINUTE), 3.0, 56.00, 'delivered', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(17, 2814, 2, DATE_SUB(NOW(), INTERVAL 30 MINUTE), DATE_SUB(NOW(), INTERVAL 10 MINUTE), 2.6, 52.00, 'delivered', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(18, 2815, 3, DATE_SUB(NOW(), INTERVAL 25 MINUTE), DATE_SUB(NOW(), INTERVAL 5 MINUTE), 1.9, 46.00, 'delivered', DATE_SUB(NOW(), INTERVAL 45 MINUTE));

-- -----------------------------------------------------------------------------
-- 14. REVIEWS
-- -----------------------------------------------------------------------------
INSERT INTO reviews (review_id, order_id, customer_id, restaurant_id, partner_id, restaurant_rating, partner_rating, review_text, created_at) VALUES
(1, 2801, 1, 1, 1, 5, 5, 'The Dum Biryani was exceptionally fragrant and meat was melt-in-the-mouth. Ravi was super swift!', DATE_SUB(NOW(), INTERVAL 300 MINUTE)),
(2, 2802, 2, 2, 2, 5, 5, 'Best crispy ghee roast in Bengaluru. Arrived piping hot with fresh coconut chutney.', DATE_SUB(NOW(), INTERVAL 250 MINUTE)),
(3, 2803, 3, 3, 3, 4, 5, 'Great kathi rolls with proper smoky tandoori flavor. Packaging was sturdy.', DATE_SUB(NOW(), INTERVAL 235 MINUTE)),
(4, 2804, 4, 4, 1, 5, 4, 'Authentic Rajasthani thali. Dal baati was heavenly and quantity was generous.', DATE_SUB(NOW(), INTERVAL 185 MINUTE)),
(5, 2805, 5, 5, 4, 5, 5, 'Saffron phirni and rasmalai were divine. Not overly sweet, perfect balance.', DATE_SUB(NOW(), INTERVAL 190 MINUTE)),
(6, 2806, 6, 1, 2, 4, 5, 'Biryani was flavorful. Great portion size for dinner.', DATE_SUB(NOW(), INTERVAL 170 MINUTE)),
(7, 2807, 7, 2, 3, 5, 5, 'Filter coffee stayed boiling hot. Mysore masala dosa had crisp red chutney.', DATE_SUB(NOW(), INTERVAL 135 MINUTE)),
(8, 2808, 8, 3, 4, 5, 4, 'Butter chicken was rich and creamy without being greasy. Tandoori naans were soft.', DATE_SUB(NOW(), INTERVAL 115 MINUTE));

-- -----------------------------------------------------------------------------
-- 15. AUDIT LOG (Status Transition History)
-- Triggers automatically capture initial order creation and status changes.
-- We also insert specific narrative transition notes without fixed log_ids:
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (order_id, old_status, new_status, changed_by_user_id, change_notes, created_at) VALUES
(2841, 'Placed', 'Accepted', 11, 'Restaurant kitchen accepted order', DATE_SUB(NOW(), INTERVAL 12 MINUTE)),
(2841, 'Accepted', 'Preparing', 11, 'Chefs began preparing Dum Biryani', DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(2841, 'Preparing', 'Ready', 11, 'Order packed and placed in dispatch bay', DATE_SUB(NOW(), INTERVAL 1 MINUTE)),
(2840, 'Placed', 'Accepted', 11, 'Order accepted by Ember & Rice', DATE_SUB(NOW(), INTERVAL 9 MINUTE)),
(2840, 'Accepted', 'Preparing', 11, 'Cooking 3x Veg Biryani', DATE_SUB(NOW(), INTERVAL 8 MINUTE)),
(2839, 'Placed', 'Accepted', 11, 'Order accepted by Ember & Rice', DATE_SUB(NOW(), INTERVAL 12 MINUTE)),
(2839, 'Accepted', 'Preparing', 11, 'Simmering Mutton Biryani', DATE_SUB(NOW(), INTERVAL 11 MINUTE));
