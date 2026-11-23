# Dabba: Online Food Ordering System - Entity Relationship (ER) Diagram

This document contains the complete Entity-Relationship model for the **Dabba** Online Food Ordering System. The schema is designed in Third Normal Form (3NF) to support a unified multi-role workflow (Customer, Restaurant, Delivery Partner) over a single MySQL 8 database.

---

## Mermaid ER Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned to"
    USERS ||--o| CUSTOMERS : "is a"
    USERS ||--o| RESTAURANTS : "manages"
    USERS ||--o| DELIVERY_PARTNERS : "drives for"

    CUSTOMERS ||--o{ ADDRESSES : "saves"
    CUSTOMERS ||--o{ ORDERS : "places"
    CUSTOMERS ||--o{ REVIEWS : "writes"

    RESTAURANTS ||--o{ MENU_ITEMS : "offers"
    RESTAURANTS ||--o{ ORDERS : "receives"
    RESTAURANTS ||--o{ REVIEWS : "evaluated in"

    CATEGORIES ||--o{ MENU_ITEMS : "classifies"

    COUPONS ||--o{ ORDERS : "applied to"

    ORDERS ||--|{ ORDER_ITEMS : "contains"
    ORDERS ||--|| PAYMENTS : "billed via"
    ORDERS ||--o| DELIVERIES : "fulfilled by"
    ORDERS ||--o| REVIEWS : "rated in"
    ORDERS ||--o{ AUDIT_LOG : "tracked by"

    MENU_ITEMS ||--o{ ORDER_ITEMS : "selected in"

    DELIVERY_PARTNERS ||--o{ ORDERS : "assigned to"
    DELIVERY_PARTNERS ||--o{ DELIVERIES : "executes"
    DELIVERY_PARTNERS ||--o{ REVIEWS : "rated in"

    ROLES {
        int role_id PK
        string role_name UK "customer | restaurant | delivery_partner"
        string description
    }

    USERS {
        int user_id PK
        int role_id FK
        string full_name
        string email UK
        string phone UK
        string password_hash
        boolean is_active
        datetime created_at
    }

    CUSTOMERS {
        int customer_id PK
        int user_id FK,UK
        int loyalty_points
        datetime created_at
    }

    ADDRESSES {
        int address_id PK
        int customer_id FK
        string label "Home | Work | Other"
        string address_line
        string landmark
        string city
        string postal_code
        decimal latitude
        decimal longitude
        boolean is_default
    }

    RESTAURANTS {
        int restaurant_id PK
        int user_id FK,UK
        string name
        string tagline
        string cuisine_type
        decimal rating
        int total_ratings
        int prep_time_min
        boolean is_accepting_orders
        string address
        string phone
        string accent_color
    }

    CATEGORIES {
        int category_id PK
        string name UK "Biryani | Dosa | Thali | etc."
        int display_order
    }

    MENU_ITEMS {
        int item_id PK
        int restaurant_id FK
        int category_id FK
        string name
        string description
        decimal price
        boolean is_veg
        boolean is_available
        int stock_quantity
        string image_letter
        string badge_bg
        string badge_text
    }

    COUPONS {
        int coupon_id PK
        string code UK "DABBA50 | FEAST100 | etc."
        decimal discount_percentage
        decimal flat_discount
        decimal max_discount
        decimal min_order_amount
        boolean is_active
        datetime valid_until
    }

    ORDERS {
        int order_id PK
        int customer_id FK
        int restaurant_id FK
        int delivery_partner_id FK
        int address_id FK
        int coupon_id FK
        enum order_status "Placed | Accepted | Preparing | Ready | Picked up | Delivered | Cancelled | Rejected"
        decimal subtotal
        decimal discount_amount
        decimal delivery_fee
        decimal tax_amount
        decimal total_amount
        string special_instructions
        int estimated_delivery_minutes
        datetime placed_at
        datetime accepted_at
        datetime ready_at
        datetime picked_at
        datetime delivered_at
        datetime cancelled_at
    }

    ORDER_ITEMS {
        int order_item_id PK
        int order_id FK
        int item_id FK
        string item_name
        decimal unit_price
        int quantity
        decimal item_total
    }

    PAYMENTS {
        int payment_id PK
        int order_id FK,UK
        enum payment_method "online | cod"
        enum payment_status "Pending | Completed | Failed | Refunded"
        string transaction_reference UK
        decimal amount
        datetime paid_at
    }

    DELIVERY_PARTNERS {
        int partner_id PK
        int user_id FK,UK
        string vehicle_type
        string vehicle_number
        boolean is_online
        enum current_status "available | busy | offline"
        decimal current_lat
        decimal current_lng
        int total_trips
        decimal total_earnings
        decimal hours_online
        decimal rating
    }

    DELIVERIES {
        int delivery_id PK
        int order_id FK,UK
        int partner_id FK
        datetime pickup_time
        datetime delivery_time
        decimal distance_km
        decimal delivery_fee_earned
        enum status "assigned | picked_up | delivered | cancelled"
    }

    REVIEWS {
        int review_id PK
        int order_id FK,UK
        int customer_id FK
        int restaurant_id FK
        int partner_id FK
        int restaurant_rating "1 to 5"
        int partner_rating "1 to 5"
        string review_text
        datetime created_at
    }

    AUDIT_LOG {
        int log_id PK
        int order_id FK
        string old_status
        string new_status
        int changed_by_user_id FK
        string change_notes
        datetime created_at
    }
```

---

## Relationship Cardinalities Summary

| Parent Entity | Child Entity | Cardinality | Business Meaning / Integrity Rule |
|---|---|---|---|
| `roles` | `users` | 1 : N | Each role classifies multiple system users; users have exactly one role. |
| `users` | `customers` | 1 : 1 | Customer profiles are subtypes of users (ON DELETE CASCADE). |
| `users` | `restaurants` | 1 : 1 | Restaurant owner profiles are subtypes of users (ON DELETE CASCADE). |
| `users` | `delivery_partners` | 1 : 1 | Delivery rider profiles are subtypes of users (ON DELETE CASCADE). |
| `customers` | `addresses` | 1 : N | Customers can save multiple delivery addresses (Home, Work, etc.). |
| `customers` | `orders` | 1 : N | Customers place zero or more food orders. |
| `restaurants` | `menu_items` | 1 : N | Each restaurant manages their own dishes and live stock levels. |
| `categories` | `menu_items` | 1 : N | Generic categories group dishes across restaurants. |
| `orders` | `order_items` | 1 : N | Each order contains one or more line items (composite details). |
| `orders` | `payments` | 1 : 1 | Exactly one payment record exists per order. |
| `orders` | `deliveries` | 1 : 1 | Exactly one delivery assignment record per order. |
| `orders` | `reviews` | 1 : 1 | At most one verified review can be submitted per order. |
| `orders` | `audit_log` | 1 : N | Every status transition is automatically tracked by MySQL triggers. |

