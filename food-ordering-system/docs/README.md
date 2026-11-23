# Dabba: Online Food Ordering System 🍲

> A unified, full-stack college DBMS project featuring a single MySQL 8 database, Flask REST backend, and responsive vanilla JS frontends for **Customers**, **Restaurants**, and **Delivery Partners**.

---

## 1. Project Overview

**Dabba** is an online food ordering platform built specifically to demonstrate relational database principles, transactions, triggers, stored procedures, normalized schemas, and analytic window functions.

Unlike traditional fragmented applications, Dabba uses:
- **One unified database (`dabba_db`) in 3NF** with 15 relational tables.
- **One single backend server** with role-based access control (RBAC).
- **Three live working interfaces** based on custom UI designs:
  1. **Customer App** (Mobile layout): 3D rotating carousel, live order tracking with 5s polling, search/filters, cart drawer, and review system.
  2. **Restaurant Kitchen Dashboard** (Desktop layout): 3-column live Kanban board (New / Preparing / Ready), order actions, low stock switches, today's KPIs, and real hourly order bar chart.
  3. **Delivery Partner App** (Mobile layout): 3D map route, interactive slide-to-confirm pickup/drop control, online toggle, and live payout earnings.

---

## 2. Tech Stack

- **Database:** MySQL 8.0+
- **Backend:** Python 3.10+, Flask 3.1+, `mysql-connector-python` (100% parameterized queries), Werkzeug password hashing.
- **Frontend:** Vanilla HTML5, CSS3 animations, Vanilla JavaScript (Fetch API).
- **Configuration:** `.env` file management for database and session credentials.

---

## 3. Demo Credentials

All demo accounts use the standard password: **`password123`**

| Role | Email | Password | Name / Entity | Purpose |
|---|---|---|---|---|
| **Customer** | `customer@dabba.com` | `password123` | Aarav Sharma | Browse restaurants, add items to cart, track orders live |
| **Restaurant** | `restaurant@dabba.com` | `password123` | Ember & Rice Kitchen | Manage kitchen, accept/reject, mark ready, toggle stocks |
| **Delivery Partner** | `delivery@dabba.com` | `password123` | Ravi Kumar | Receive assignments, slide-to-confirm pickup & delivery |

*(Additional customer accounts: `ananya@dabba.com`, `rohan@dabba.com`, `pooja@dabba.com`, `karthik@dabba.com`. Additional restaurants: `dosa@dabba.com`, `delhi@dabba.com`, `thali@dabba.com`, `sweets@dabba.com`)*

---

## 4. Setup and Installation Instructions

### Prerequisites
1. **Python 3.10+** installed.
2. **MySQL Server 8.0+** running locally on port `3306`.

### Step 1: Clone / Navigate to Project Directory
```powershell
cd "c:\Users\koush\OneDrive\Desktop\SEM 3 PROJECTS\DBMS project\food-ordering-system"
```

### Step 2: Configure Environment Variables
Verify or edit `backend/.env` with your MySQL root password:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=dabba_db
SECRET_KEY=dabba_super_secret_session_key_2026_sem3_dbms
PORT=5000
DEBUG=True
```

### Step 3: Initialize Database Schema & Seed Data
Execute the provided SQL scripts using the MySQL client:
```powershell
mysql -h 127.0.0.1 -u root -p dabba_db < database/schema.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/triggers_procedures.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/views.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/seed.sql
```

*(Optional) Test complex demonstration queries:*
```powershell
mysql -h 127.0.0.1 -u root -p dabba_db < database/queries.sql
```

### Step 4: Install Python Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 5: Start the Server
```powershell
cd backend
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 5. Automated Verification Test Suite

Run the end-to-end integration test suite verifying the complete order lifecycle from order placement to customer review:
```powershell
cd backend
python test_e2e.py
```

---

## 6. Database Architecture & Highlights

### 6.1 Database Schema (3NF)
1. **`roles`**: System roles (`customer`, `restaurant`, `delivery_partner`).
2. **`users`**: Master authentication entity with hashed passwords and unique emails/phones.
3. **`customers`**: Subtype linked 1:1 with users; stores loyalty points.
4. **`addresses`**: 1:N saved addresses per customer with default flags and coordinates.
5. **`restaurants`**: 1:1 linked with users; ratings, prep times, cuisine types.
6. **`categories`**: Food categories (`Biryani`, `Dosa`, `Thali`, `Kebabs`, etc.).
7. **`menu_items`**: Dish specifications, pricing, veg/non-veg flags, stock counts, UI badges.
8. **`coupons`**: Discount codes (`DABBA50`, `FEAST100`, etc.) with validation constraints.
9. **`delivery_partners`**: Rider fleet metrics, vehicles, live availability, earnings.
10. **`orders`**: Transaction root entity with composite status workflow and pricing.
11. **`order_items`**: Line-item breakdown linking orders to dishes with historical prices.
12. **`payments`**: Payment records (`online`, `cod`), status (`Completed`, `Refunded`).
13. **`deliveries`**: Order fulfillment tasks, tracking pickups, drops, and rider fees.
14. **`reviews`**: Ratings (1 to 5) and feedback for restaurants and delivery partners.
15. **`audit_log`**: Automated tracking of all order status transitions.

### 6.2 Stored Procedures
- **`place_order(...)`**:
  Executes in a safe `START TRANSACTION` with `COMMIT` / `ROLLBACK`. Validates customer and restaurant availability, checks and calculates coupon discounts, creates the order, inserts line items in a loop, creates payment record, and auto-assigns the nearest available delivery partner.
- **`cancel_order(...)`**:
  Validates that order is in a cancellable state (`Placed` or `Accepted`). Updates order status to `Cancelled`, issues refund record in `payments`, restores inventory in `menu_items`, and releases the delivery partner.
- **`monthly_sales_report(...)`**:
  Aggregates total orders, gross food sales, discounts given, tax collected, and net revenue for any restaurant by month and year.

### 6.3 Triggers
- **`trg_reduce_stock_after_order`**: Decrements dish stock quantity upon item insertion; sets `is_available = 0` if stock reaches zero.
- **`trg_recalculate_order_total_insert`**: Recalculates subtotal, 5% GST tax, and total amount when items are added to an order.
- **`trg_order_status_audit`**: Automatically inserts a log entry into `audit_log` whenever an order transitions between statuses.

### 6.4 Relational Views
- **`top_selling_items`**: Aggregates quantities sold, total revenue, and order frequencies per dish.
- **`restaurant_revenue`**: Summarizes gross sales, discounts, and average ticket sizes per restaurant.
- **`customer_order_summary`**: 360-degree customer metrics including completed orders, total spending, and last order date.

### 6.5 Example SQL Queries (`database/queries.sql`)
1. **Multi-table JOIN:** Joins Orders, Customers, Users, Restaurants, Payments, and Deliveries.
2. **Correlated Subquery:** Dishes priced above their restaurant's own average dish price.
3. **Non-correlated Subquery:** High-spending customers who redeemed promotional coupons.
4. **GROUP BY & HAVING:** Restaurants with at least 3 completed deliveries and over ₹1,000 in sales.
5. **Window Function `RANK()`:** Real-time revenue ranking of restaurants.
6. **Window Function `DENSE_RANK()`:** Dish price tiers partitioned by category.

---

## 7. Folder Structure

```
food-ordering-system/
├── design/                         # Reference static mockups (kept intact)
│   ├── dabba-customer.html
│   ├── dabba-restaurant.html
│   └── dabba-delivery.html
├── database/                       # Graded database artifacts
│   ├── schema.sql                  # 3NF DDL, tables, constraints, indexes
│   ├── triggers_procedures.sql     # Stored procedures & automated triggers
│   ├── views.sql                   # 3 business intelligence views
│   ├── seed.sql                    # Realistic Indian seed data (5 rests, 47 items, 30+ orders)
│   └── queries.sql                 # JOINs, subqueries, GROUP BY/HAVING, RANK()
├── backend/                        # Single Flask backend
│   ├── app.py                      # Main entry point & routing
│   ├── db.py                       # Parameterized DB helper
│   ├── auth.py                     # Authentication & role-based access control
│   ├── customer_routes.py          # Customer APIs & page handlers
│   ├── restaurant_routes.py        # Restaurant kitchen APIs & page handlers
│   ├── delivery_routes.py          # Delivery rider APIs & page handlers
│   ├── test_e2e.py                 # Automated end-to-end integration test
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Active environment credentials
│   └── .env.example                # Template credentials
├── frontend/                       # Jinja templates & static files
│   └── templates/
│       ├── auth/                   # login.html, signup.html
│       ├── customer/               # index.html
│       ├── restaurant/             # index.html
│       └── delivery/               # index.html
└── docs/                           # Documentation for academic grading
    ├── ER_DIAGRAM.md               # Mermaid ER diagram & cardinality table
    ├── NORMALIZATION.md            # 1NF, 2NF, 3NF explanations & anomaly analysis
    └── README.md                   # Complete system manual
```

