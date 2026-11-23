import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'food-ordering-system', 'backend'))
from db import get_connection

def clear_order_history():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        print("Disabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        tables_to_truncate = [
            'order_items',
            'payments',
            'deliveries',
            'delivery_rejections',
            'reviews',
            'audit_log',
            'orders'
        ]
        
        for table in tables_to_truncate:
            print(f"Truncating {table}...")
            cursor.execute(f"TRUNCATE TABLE {table};")
            
        print("Resetting orders AUTO_INCREMENT to 1001...")
        cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1001;")
        
        print("Re-enabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        print("Resetting delivery partners to online and available...")
        cursor.execute("UPDATE delivery_partners SET is_online = 1, current_status = 'available';")
        
        print("Ensuring menu items have stock and are available...")
        cursor.execute("UPDATE menu_items SET is_available = 1, stock_quantity = 50 WHERE stock_quantity < 10;")
        
        conn.commit()
        print("Commit successful!")
        
        # Verify counts
        print("\n--- Verifying Database State ---")
        for table in ['orders', 'order_items', 'payments', 'deliveries', 'delivery_rejections', 'reviews', 'audit_log']:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table};")
            count = cursor.fetchone()['cnt']
            print(f"  {table}: {count} records")
            
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        print(f"  users (preserved): {cursor.fetchone()['cnt']} records")
        cursor.execute("SELECT COUNT(*) as cnt FROM restaurants;")
        print(f"  restaurants (preserved): {cursor.fetchone()['cnt']} records")
        cursor.execute("SELECT COUNT(*) as cnt FROM menu_items;")
        print(f"  menu_items (preserved): {cursor.fetchone()['cnt']} records")
        cursor.execute("SELECT partner_id, is_online, current_status FROM delivery_partners;")
        partners = cursor.fetchall()
        print(f"  delivery_partners reset: {partners}")

        print("\n✅ All order history deleted cleanly and database is ready for fresh demo orders!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error clearing order history: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    clear_order_history()
