"""
Database connection and execution helpers using mysql-connector-python.
All queries strictly use parameterized queries (%s) to prevent SQL injection.
Supports local MySQL, Railway, Render, TiDB Serverless, Aiven, and URL connection strings.
Includes automatic Python transaction fallbacks for engines without stored procedure support (e.g. TiDB).
"""

import os
import json
import time
import random
import urllib.parse
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for connection URLs first (common on Railway, Render, TiDB, etc.)
db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL') or os.getenv('MYSQL_PUBLIC_URL')

if db_url:
    try:
        parsed = urllib.parse.urlparse(db_url)
        DB_HOST = parsed.hostname
        DB_PORT = parsed.port or 3306
        DB_USER = parsed.username
        DB_PASSWORD = parsed.password
        DB_NAME = parsed.path.lstrip('/')
    except Exception:
        DB_HOST = '127.0.0.1'
        DB_PORT = 3306
        DB_USER = 'root'
        DB_PASSWORD = ''
        DB_NAME = 'dabba_db'
else:
    DB_HOST = os.getenv('DB_HOST') or os.getenv('MYSQLHOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT') or os.getenv('MYSQLPORT', '3306'))
    DB_USER = os.getenv('DB_USER') or os.getenv('MYSQLUSER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('MYSQLPASSWORD', '')
    DB_NAME = os.getenv('DB_NAME') or os.getenv('MYSQLDATABASE', 'dabba_db')

DB_SSL_DISABLED = os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true'

def get_connection():
    """Establish and return a new MySQL database connection."""
    kwargs = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME,
        'autocommit': False,
        'charset': 'utf8mb4'
    }
    if DB_SSL_DISABLED:
        kwargs['ssl_disabled'] = True
    elif DB_HOST not in ('127.0.0.1', 'localhost'):
        # For cloud MySQL like TiDB, Aiven, or Railway public, enable TLS/SSL
        kwargs['ssl_verify_cert'] = False
        kwargs['ssl_verify_identity'] = False
        
    return mysql.connector.connect(**kwargs)

def query_db(query, params=(), one=False, commit=False):
    """
    Execute a parameterized SQL query safely.
    :param query: SQL string containing %s placeholders
    :param params: tuple or list of parameters
    :param one: if True, returns a single dictionary row or None
    :param commit: if True, commits transaction and returns lastrowid / affected_rows
    :return: list of dicts, single dict, or dict with metadata if commit
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            cursor.close()
            return {'lastrowid': last_id, 'rowcount': affected}
        
        result = cursor.fetchall()
        cursor.close()
        return (result[0] if result else None) if one else result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _fallback_place_order(args, conn):
    """Python transaction fallback for place_order on engines without stored procedures (e.g. TiDB)."""
    p_customer_id, p_restaurant_id, p_address_id, p_coupon_code, p_payment_method, p_special_instructions, p_items_json, _, _ = args
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Customer verification
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (p_customer_id,))
        if not cursor.fetchone():
            return {'place_order_arg8': None, 'place_order_arg9': 'Error: Invalid customer account.'}

        # 2. Restaurant verification
        cursor.execute("SELECT is_accepting_orders, prep_time_min FROM restaurants WHERE restaurant_id = %s", (p_restaurant_id,))
        rest = cursor.fetchone()
        if not rest or not rest.get('is_accepting_orders'):
            return {'place_order_arg8': None, 'place_order_arg9': 'Error: Restaurant is currently not accepting orders.'}
        est_min = (rest.get('prep_time_min') or 25) + 15

        # 3. Address verification
        cursor.execute("SELECT address_id FROM addresses WHERE address_id = %s AND customer_id = %s", (p_address_id, p_customer_id))
        if not cursor.fetchone():
            return {'place_order_arg8': None, 'place_order_arg9': 'Error: Address does not belong to customer.'}

        # 4. Coupon check
        coupon_id = None
        disc_pct, flat_disc, min_order, max_disc = 0, 0, 0, 9999.0
        if p_coupon_code:
            cursor.execute("""
                SELECT coupon_id, discount_percentage, flat_discount_amount, min_order_amount, max_discount_amount
                FROM coupons
                WHERE code = %s AND is_active = 1 AND valid_until >= NOW() AND (usage_limit IS NULL OR times_used < usage_limit)
            """, (p_coupon_code,))
            c_row = cursor.fetchone()
            if c_row:
                coupon_id = c_row['coupon_id']
                disc_pct = float(c_row['discount_percentage'] or 0)
                flat_disc = float(c_row['flat_discount_amount'] or 0)
                min_order = float(c_row['min_order_amount'] or 0)
                max_disc = float(c_row['max_discount_amount'] or 9999.0)

        # 5. Parse items and compute subtotal
        items = json.loads(p_items_json) if isinstance(p_items_json, str) else p_items_json
        subtotal = 0.0
        validated_items = []
        for itm in items:
            item_id = int(itm.get('item_id'))
            qty = int(itm.get('quantity', 1))
            cursor.execute("SELECT item_id, name, price, is_available, stock_quantity FROM menu_items WHERE item_id = %s AND restaurant_id = %s", (item_id, p_restaurant_id))
            m_row = cursor.fetchone()
            if not m_row or not m_row.get('is_available'):
                conn.rollback()
                name = m_row.get('name') if m_row else f"Item {item_id}"
                return {'place_order_arg8': None, 'place_order_arg9': f'Error: {name} is currently unavailable.'}
            if (m_row.get('stock_quantity') or 0) < qty:
                conn.rollback()
                return {'place_order_arg8': None, 'place_order_arg9': f"Error: Insufficient stock for {m_row['name']}."}
            
            price = float(m_row['price'])
            item_total = round(price * qty, 2)
            subtotal += item_total
            validated_items.append((item_id, m_row['name'], price, qty, item_total))

        # Apply coupon
        computed_discount = 0.0
        if coupon_id and subtotal >= min_order:
            if disc_pct > 0:
                computed_discount = min(max_disc, round(subtotal * (disc_pct / 100.0), 2))
            elif flat_disc > 0:
                computed_discount = min(max_disc, flat_disc)

        tax = round(subtotal * 0.05, 2)
        delivery_fee = 40.0
        total_amount = max(0.0, round(subtotal - computed_discount + delivery_fee + tax, 2))

        # Insert order
        cursor.execute("""
            INSERT INTO orders (
                customer_id, restaurant_id, delivery_address_id, coupon_id,
                subtotal, discount_amount, delivery_fee, tax_amount, total_amount,
                special_instructions, estimated_delivery_minutes, order_status, placed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Placed', NOW())
        """, (
            p_customer_id, p_restaurant_id, p_address_id, coupon_id,
            subtotal, computed_discount, delivery_fee, tax, total_amount,
            p_special_instructions, est_min
        ))
        order_id = cursor.lastrowid

        # Insert items & decrease stock
        for v_item_id, v_name, v_price, v_qty, v_total in validated_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity, item_total)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, v_item_id, v_name, v_price, v_qty, v_total))
            cursor.execute("""
                UPDATE menu_items
                SET stock_quantity = GREATEST(0, stock_quantity - %s),
                    is_available = CASE WHEN stock_quantity - %s <= 0 THEN 0 ELSE is_available END
                WHERE item_id = %s
            """, (v_qty, v_qty, v_item_id))

        if coupon_id:
            cursor.execute("UPDATE coupons SET times_used = times_used + 1 WHERE coupon_id = %s", (coupon_id,))

        # Record payment
        txn_ref = f"TXN-{int(time.time())}-{random.randint(1000, 9999)}"
        pay_method = 'cod' if (p_payment_method or '').lower() == 'cod' else 'online'
        cursor.execute("""
            INSERT INTO payments (order_id, payment_method, payment_status, transaction_reference, amount, paid_at)
            VALUES (%s, %s, 'Completed', %s, %s, NOW())
        """, (order_id, pay_method, txn_ref, total_amount))

        # Audit log
        cursor.execute("""
            INSERT INTO audit_log (order_id, old_status, new_status, change_notes, created_at)
            VALUES (%s, NULL, 'Placed', 'New order placed successfully', NOW())
        """, (order_id,))

        conn.commit()
        return {'place_order_arg8': order_id, 'place_order_arg9': 'Order placed successfully!'}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def _fallback_cancel_order(args, conn):
    """Python transaction fallback for cancel_order on engines without stored procedures (e.g. TiDB)."""
    p_order_id, p_user_id, p_reason, _, _ = args
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT order_id, order_status, delivery_partner_id FROM orders WHERE order_id = %s", (p_order_id,))
        ord_row = cursor.fetchone()
        if not ord_row:
            return {'cancel_order_arg4': 0, 'cancel_order_arg5': 'Error: Order does not exist.'}

        curr_status = ord_row['order_status']
        if curr_status not in ('Placed', 'Accepted', 'Preparing'):
            return {'cancel_order_arg4': 0, 'cancel_order_arg5': f'Error: Cannot cancel order in {curr_status} state.'}

        cursor.execute("UPDATE orders SET order_status = 'Cancelled', cancelled_at = NOW() WHERE order_id = %s", (p_order_id,))

        # Restore inventory
        cursor.execute("SELECT item_id, quantity FROM order_items WHERE order_id = %s", (p_order_id,))
        for item in cursor.fetchall():
            cursor.execute("""
                UPDATE menu_items
                SET stock_quantity = stock_quantity + %s, is_available = 1
                WHERE item_id = %s
            """, (item['quantity'], item['item_id']))

        # Refund payment
        cursor.execute("UPDATE payments SET payment_status = 'Refunded' WHERE order_id = %s", (p_order_id,))

        # Free delivery partner if assigned
        partner_id = ord_row.get('delivery_partner_id')
        if partner_id:
            cursor.execute("UPDATE delivery_partners SET is_available = 1 WHERE partner_id = %s", (partner_id,))
            cursor.execute("UPDATE deliveries SET delivery_status = 'Cancelled' WHERE order_id = %s", (p_order_id,))

        # Audit log
        cursor.execute("""
            INSERT INTO audit_log (order_id, old_status, new_status, change_notes, created_at)
            VALUES (%s, %s, 'Cancelled', %s, NOW())
        """, (p_order_id, curr_status, p_reason or 'Order cancelled'))

        conn.commit()
        return {'cancel_order_arg4': 1, 'cancel_order_arg5': 'Order cancelled successfully.'}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def call_procedure(proc_name, args=()):
    """
    Call a MySQL stored procedure safely using parameterized arguments.
    Gracefully falls back to pure Python transaction if stored procedures are unsupported (e.g. TiDB).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        result = cursor.callproc(proc_name, args)
        conn.commit()
        cursor.close()
        return result
    except Exception as e:
        # If procedure does not exist or procedures not supported by the database engine
        err_str = str(e).lower()
        if 'does not exist' in err_str or 'not supported' in err_str or '1305' in err_str or '8108' in err_str:
            if proc_name == 'place_order':
                return _fallback_place_order(args, conn)
            elif proc_name == 'cancel_order':
                return _fallback_cancel_order(args, conn)
        conn.rollback()
        raise e
    finally:
        conn.close()
