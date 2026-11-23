# Database Normalization Report: Dabba Food Ordering System

## 1. Executive Summary & Objective

In relational database design, **Normalization** is the systematic process of organizing data to eliminate data redundancy (duplicate information) and undesirable anomalies during data manipulation (**Insertion**, **Update**, and **Deletion** anomalies).

The **Dabba** database schema was designed from first principles and normalized up to the **Third Normal Form (3NF)** while respecting real-world performance considerations (such as capturing historical price snapshots for financial accounting).

---

## 2. Normalization Steps Breakdown

### 2.1 First Normal Form (1NF)
**Requirements:**
1. Each column must contain atomic (indivisible) values.
2. No repeating groups or arrays stored in single cells.
3. Each table must have a distinct Primary Key (PK) to uniquely identify each row.

**Violations Avoided:**
- *Anti-pattern:* Storing ordered dishes as a comma-separated string within the `orders` table (e.g., `dishes = "Dum Biryani (2), Butter Naan (1)"`).
  *Solution:* Extracted all order items into a distinct relational bridge table `order_items`, where every line item is an atomic record with its own `order_item_id`, `item_id`, `unit_price`, and `quantity`.
- *Anti-pattern:* Storing multiple addresses as comma-separated values in `customers`.
  *Solution:* Extracted addresses into `addresses` table, linked via foreign key `customer_id`.

**1NF State:**
All attributes across all 15 tables (`users`, `roles`, `customers`, `addresses`, `restaurants`, `categories`, `menu_items`, `orders`, `order_items`, `payments`, `delivery_partners`, `deliveries`, `coupons`, `reviews`, `audit_log`) are atomic and single-valued with explicit Primary Keys.

---

### 2.2 Second Normal Form (2NF)
**Requirements:**
1. The relation must be in **1NF**.
2. **No Partial Functional Dependencies**: No non-prime attribute may depend on only a subset of any candidate composite key. Every non-prime attribute must depend on the *entire* candidate key.

**Analysis in Dabba:**
- In tables with single-column surrogate primary keys (`user_id`, `restaurant_id`, `coupon_id`, `order_id`, etc.), partial dependencies are mathematically impossible because the primary key cannot be decomposed into a proper subset.
- For `order_items`:
  * Composite candidate key: `(order_id, item_id)`.
  * Attributes: `unit_price`, `quantity`, `item_total`.
  * If restaurant details (such as `restaurant_name` or `cuisine_type`) were stored in `order_items`, they would depend only on `item_id` (a partial dependency), violating 2NF.
  * In Dabba, `order_items` stores strictly `(order_item_id PK, order_id FK, item_id FK, item_name, unit_price, quantity, item_total)`. All restaurant metadata resides strictly in `restaurants`, eliminating partial dependencies.

---

### 2.3 Third Normal Form (3NF)
**Requirements:**
1. The relation must be in **2NF**.
2. **No Transitive Functional Dependencies**: Non-prime attributes must not depend on other non-prime attributes ($X \to Y$ and $Y \to Z$ where $Z$ is non-prime and $Y$ is not a superkey). Informally: *"Every non-key attribute must provide a fact about the key, the whole key, and nothing but the key."*

**Specific 3NF Decompositions Applied in Dabba:**

#### Case 1: User Roles Decomposition
- *Transitive Dependency:* `user_id -> role_id -> role_name, role_description`.
- If `role_name` was kept in `users`, changing a role description or renaming a role would require updating multiple rows (Update Anomaly).
- *Resolution:* Decomposed into `roles (role_id PK, role_name, description)` and `users (user_id PK, role_id FK, ...)`.

#### Case 2: Categories and Menu Items
- *Transitive Dependency:* `item_id -> category_id -> category_name, display_order`.
- *Resolution:* Category details are isolated in `categories (category_id PK, name, display_order)`. `menu_items` references only `category_id FK`.

#### Case 3: Customer Addresses
- *Transitive Dependency:* `customer_id -> address_id -> (address_line, postal_code, city)`.
- Customers frequently have multiple addresses (Home, Office, Parents). Storing address fields in `customers` violates 3NF and causes update anomalies.
- *Resolution:* Separated into `addresses (address_id PK, customer_id FK, label, address_line, ...)`.

#### Case 4: Discount Coupons
- *Transitive Dependency:* `order_id -> coupon_id -> (code, discount_percentage, max_discount, min_order_amount)`.
- *Resolution:* Coupon configuration is stored once in `coupons`. When an order is placed, `orders` references `coupon_id FK` and stores only the resulting monetary impact (`discount_amount`).

#### Case 5: Temporal Immutability & Point-in-Time Accounting
- In `order_items`, `unit_price` and `item_name` are recorded at the exact moment the order is placed.
- *DBMS Rationale:* If `order_items` dynamically read `menu_items.price`, any future price increase by the restaurant would illegally alter past financial records and customer receipts. Preserving the historical snapshot in `order_items` ensures temporal integrity and audit compliance.

---

## 3. Anomaly Elimination Summary

| Relational Anomaly | Scenario without 3NF | How Dabba Schema Resolves It |
|---|---|---|
| **Insertion Anomaly** | Cannot create a new dish category without first assigning a menu item to it. | `categories` table allows adding categories independently of menu items. |
| **Update Anomaly** | Changing delivery partner vehicle or phone number requires updating all historical orders they fulfilled. | Rider details live in `delivery_partners` and `users`. Updating once reflects across all references. |
| **Deletion Anomaly** | Deleting a customer deletes historical revenue analytics and order accounting records. | `orders.customer_id` uses `ON DELETE RESTRICT`, preventing accidental removal of historical financial transactions. |

---

## 4. Conclusion

The Dabba database schema satisfies the requirements of **Third Normal Form (3NF)**. It ensures:
1. High data integrity with foreign key cascade/restrict constraints.
2. Zero data redundancy across user profiles, restaurants, categories, and promotions.
3. Fast execution of relational queries and analytical views (`top_selling_items`, `restaurant_revenue`, `customer_order_summary`).

