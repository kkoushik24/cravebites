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

### Step 1: Start the Server
Navigate to the backend directory and launch the server:
```powershell
cd "c:\Users\koush\OneDrive\Desktop\SEM 3 PROJECTS\DBMS project\food-ordering-system\backend"
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

### Step 2: Database Initialization (if re-seeding)
```powershell
cd "c:\Users\koush\OneDrive\Desktop\SEM 3 PROJECTS\DBMS project\food-ordering-system"
mysql -h 127.0.0.1 -u root -p dabba_db < database/schema.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/triggers_procedures.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/views.sql
mysql -h 127.0.0.1 -u root -p dabba_db < database/seed.sql
```

---

## 5. Automated Verification Test Suite

Run the end-to-end integration test suite verifying the complete order lifecycle from order placement to customer review:
```powershell
cd "c:\Users\koush\OneDrive\Desktop\SEM 3 PROJECTS\DBMS project\food-ordering-system\backend"
python test_e2e.py
```

---

## 6. Database Documentation Links
- **[ER Diagram & Cardinality Table](file:///c:/Users/koush/OneDrive/Desktop/SEM%203%20PROJECTS/DBMS%20project/food-ordering-system/docs/ER_DIAGRAM.md)**
- **[Database Normalization Report (1NF to 3NF)](file:///c:/Users/koush/OneDrive/Desktop/SEM%203%20PROJECTS/DBMS%20project/food-ordering-system/docs/NORMALIZATION.md)**
- **[SQL Demonstration Queries](file:///c:/Users/koush/OneDrive/Desktop/SEM%203%20PROJECTS/DBMS%20project/food-ordering-system/database/queries.sql)**

