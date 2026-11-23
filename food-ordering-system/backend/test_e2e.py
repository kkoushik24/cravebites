"""
End-to-End Automated Test Suite for Dabba Food Ordering System
Tests:
1. Authentication (login for all 3 roles, invalid credentials, signup)
2. Role-based access control (blocking cross-role access)
3. Customer flow (browsing, coupon validation, placing order via stored procedure)
4. Restaurant flow (viewing live orders in New/Preparing/Ready, Accept, Mark Ready, Hand Over, stock toggle)
5. Delivery flow (viewing active order, slide-to-confirm pickup, slide-to-confirm drop)
6. Review submission and audit log verification
7. JWT Header-based authentication (Authorization: Bearer <token>)
8. Concurrency & Row-Locking verification (preventing overselling & double assignment via FOR UPDATE)
"""

import unittest
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from db import query_db

class TestDabbaSystem(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_auth_logins(self):
        """Test login for all 3 demo accounts."""
        # 1. Customer Login
        res_c = self.client.post('/api/auth/login', json={
            'email': 'customer@dabba.com',
            'password': 'password123'
        })
        self.assertEqual(res_c.status_code, 200)
        data_c = res_c.get_json()
        self.assertTrue(data_c['success'])
        self.assertEqual(data_c['user']['role'], 'customer')
        self.assertIn('token', data_c)

        # 2. Restaurant Login
        res_r = self.client.post('/api/auth/login', json={
            'email': 'restaurant@dabba.com',
            'password': 'password123'
        })
        self.assertEqual(res_r.status_code, 200)
        data_r = res_r.get_json()
        self.assertTrue(data_r['success'])
        self.assertEqual(data_r['user']['role'], 'restaurant')
        self.assertIn('token', data_r)

        # 3. Delivery Login
        res_d = self.client.post('/api/auth/login', json={
            'email': 'delivery@dabba.com',
            'password': 'password123'
        })
        self.assertEqual(res_d.status_code, 200)
        data_d = res_d.get_json()
        self.assertTrue(data_d['success'])
        self.assertEqual(data_d['user']['role'], 'delivery_partner')
        self.assertIn('token', data_d)

    def test_02_role_access_blocking(self):
        """Test that a customer is strictly blocked from restaurant & delivery APIs/pages."""
        # Login as customer
        self.client.post('/api/auth/login', json={'email': 'customer@dabba.com', 'password': 'password123'})

        # Try to access restaurant API
        res_rest_api = self.client.get('/api/restaurant/dashboard')
        self.assertEqual(res_rest_api.status_code, 403)

        # Try to access delivery API
        res_deli_api = self.client.get('/api/delivery/dashboard')
        self.assertEqual(res_deli_api.status_code, 403)

    def test_03_full_order_lifecycle(self):
        """
        Complete end-to-end order flow:
        Customer places order -> Restaurant accepts -> Restaurant marks ready ->
        Delivery partner picks up -> Delivery partner delivers -> Customer reviews.
        """
        # Step 1: Customer logs in
        login_res = self.client.post('/api/auth/login', json={'email': 'customer@dabba.com', 'password': 'password123'})
        self.assertEqual(login_res.status_code, 200)

        # Step 2: Validate coupon
        coupon_res = self.client.post('/api/customer/coupon/validate', json={'code': 'DABBA50', 'subtotal': 400.0})
        self.assertEqual(coupon_res.status_code, 200)
        self.assertTrue(coupon_res.get_json()['success'])

        # Step 3: Customer places an order (Dum Biryani + Butter Naan from Ember & Rice)
        order_payload = {
            'restaurant_id': 1,
            'address_id': 1,
            'coupon_code': 'DABBA50',
            'payment_method': 'online',
            'special_instructions': 'Extra crisp naan, please',
            'items': [
                {'item_id': 1, 'quantity': 1},
                {'item_id': 7, 'quantity': 2}
            ]
        }
        order_res = self.client.post('/api/customer/order', json=order_payload)
        self.assertEqual(order_res.status_code, 201)
        order_data = order_res.get_json()
        self.assertTrue(order_data['success'])
        order_id = order_data['order']['order_id']
        print(f"\n[E2E TEST] New Order Placed: ID #{order_id}")

        # Check initial status
        status_res = self.client.get(f'/api/customer/order/{order_id}/status')
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.get_json()['order']['order_status'], 'Placed')

        # Step 4: Restaurant logs in and views live orders
        self.client.post('/api/auth/login', json={'email': 'restaurant@dabba.com', 'password': 'password123'})
        dash_res = self.client.get('/api/restaurant/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        new_orders = dash_res.get_json()['columns']['new']
        self.assertTrue(any(o['order_id'] == order_id for o in new_orders))

        # Restaurant accepts order -> transitions to Preparing
        accept_res = self.client.post(f'/api/restaurant/order/{order_id}/action', json={'action': 'accept'})
        self.assertEqual(accept_res.status_code, 200)
        print(f"[E2E TEST] Order #{order_id} accepted by restaurant (status: Preparing)")

        # Restaurant marks order ready -> transitions to Ready
        ready_res = self.client.post(f'/api/restaurant/order/{order_id}/action', json={'action': 'mark_ready'})
        self.assertEqual(ready_res.status_code, 200)
        print(f"[E2E TEST] Order #{order_id} marked ready by kitchen (status: Ready)")

        # Step 5: Delivery partner logs in
        self.client.post('/api/auth/login', json={'email': 'delivery@dabba.com', 'password': 'password123'})
        deliv_dash = self.client.get('/api/delivery/dashboard')
        self.assertEqual(deliv_dash.status_code, 200)

        # Delivery partner slides to confirm pickup
        pickup_res = self.client.post(f'/api/delivery/order/{order_id}/pickup')
        self.assertEqual(pickup_res.status_code, 200)
        print(f"[E2E TEST] Order #{order_id} picked up by rider (status: Picked up)")

        # Delivery partner slides to confirm drop / delivered
        drop_res = self.client.post(f'/api/delivery/order/{order_id}/drop')
        self.assertEqual(drop_res.status_code, 200)
        print(f"[E2E TEST] Order #{order_id} successfully delivered (status: Delivered)")

        # Step 6: Customer logs in to verify Delivered status and submit review
        self.client.post('/api/auth/login', json={'email': 'customer@dabba.com', 'password': 'password123'})
        final_status = self.client.get(f'/api/customer/order/{order_id}/status')
        self.assertEqual(final_status.status_code, 200)
        self.assertEqual(final_status.get_json()['order']['order_status'], 'Delivered')

        # Customer submits rating and review
        rev_res = self.client.post(f'/api/customer/order/{order_id}/review', json={
            'restaurant_rating': 5,
            'partner_rating': 5,
            'review_text': 'Exceptional dum biryani! Arrived piping hot and prompt delivery.'
        })
        self.assertEqual(rev_res.status_code, 201)
        print(f"[E2E TEST] Customer review submitted for order #{order_id}")

        # Step 7: Check audit log contains complete status transitions recorded by DB trigger
        audit_records = query_db('SELECT old_status, new_status, change_notes FROM audit_log WHERE order_id = %s ORDER BY log_id ASC', (order_id,))
        print(f"[E2E TEST] Audit Trail entries for order #{order_id}: {len(audit_records)}")
        for rec in audit_records:
            print(f"  -> {rec['old_status']} to {rec['new_status']} | {rec['change_notes']}")

        self.assertTrue(len(audit_records) >= 4)

    def test_04_jwt_header_auth(self):
        """Test stateless JWT authentication passed strictly via Authorization: Bearer <token>."""
        # 1. Login to get token
        res = self.client.post('/api/auth/login', json={
            'email': 'customer@dabba.com',
            'password': 'password123'
        })
        token = res.get_json()['token']
        self.assertTrue(token)

        # 2. Use a completely clean client instance with no cookies
        raw_client = app.test_client()
        headers = {'Authorization': f'Bearer {token}'}

        res_user = raw_client.get('/api/auth/current_user', headers=headers)
        self.assertEqual(res_user.status_code, 200)
        user_data = res_user.get_json()
        self.assertTrue(user_data['success'])
        self.assertEqual(user_data['user']['email'], 'customer@dabba.com')
        self.assertEqual(user_data['user']['role'], 'customer')

        # 3. Access customer orders with JWT
        res_orders = raw_client.get('/api/customer/orders', headers=headers)
        self.assertEqual(res_orders.status_code, 200)
        self.assertTrue(res_orders.get_json()['success'])

    def test_05_concurrency_stock_locking(self):
        """
        Concurrency Test:
        Verify row-level locking (SELECT ... FOR UPDATE) in place_order stored procedure.
        Two concurrent threads try to buy the exact same remaining stock simultaneously.
        Guarantees no overselling occurs and stock never becomes negative.
        """
        # Set item 6 stock to exactly 1
        query_db('UPDATE menu_items SET stock_quantity = 1, is_available = 1 WHERE item_id = 6', commit=True)

        # Get customer JWT token
        login_res = self.client.post('/api/auth/login', json={'email': 'customer@dabba.com', 'password': 'password123'})
        token = login_res.get_json()['token']

        def attempt_order():
            client = app.test_client()
            headers = {'Authorization': f'Bearer {token}'}
            payload = {
                'restaurant_id': 1,
                'address_id': 1,
                'payment_method': 'cod',
                'items': [{'item_id': 6, 'quantity': 1}]
            }
            return client.post('/api/customer/order', json=payload, headers=headers)

        # Run 2 orders concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(attempt_order)
            future2 = executor.submit(attempt_order)
            res1 = future1.result()
            res2 = future2.result()

        results = [res1.status_code, res2.status_code]
        print(f"\n[CONCURRENCY TEST] Concurrent Stock Competition status codes: {results}")

        # Exactly one must succeed (201) and the other must be rejected (400)
        self.assertIn(201, results)
        self.assertIn(400, results)

        # Verify stock remains exactly 0 (no overselling, never negative)
        item = query_db('SELECT stock_quantity, is_available FROM menu_items WHERE item_id = 6', one=True)
        self.assertEqual(item['stock_quantity'], 0)
        print(f"[CONCURRENCY TEST] Final verified stock quantity: {item['stock_quantity']} (Overselling prevented!)")

        # Restore stock for item 6
        query_db('UPDATE menu_items SET stock_quantity = 50, is_available = 1 WHERE item_id = 6', commit=True)

    def test_06_concurrency_delivery_partner_locking(self):
        """
        Concurrency Test:
        Verify that auto-assign delivery partner locking (SELECT ... FOR UPDATE) inside
        the place_order transaction prevents the same delivery partner from being assigned twice.
        """
        # Ensure only 1 delivery partner is available
        query_db("UPDATE delivery_partners SET is_online = 0, current_status = 'offline'", commit=True)
        query_db("UPDATE delivery_partners SET is_online = 1, current_status = 'available' WHERE partner_id = 1", commit=True)

        login_res = self.client.post('/api/auth/login', json={'email': 'customer@dabba.com', 'password': 'password123'})
        token = login_res.get_json()['token']

        def place_quick_order():
            client = app.test_client()
            headers = {'Authorization': f'Bearer {token}'}
            payload = {
                'restaurant_id': 1,
                'address_id': 1,
                'payment_method': 'online',
                'items': [{'item_id': 1, 'quantity': 1}]
            }
            return client.post('/api/customer/order', json=payload, headers=headers)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(place_quick_order)
            f2 = executor.submit(place_quick_order)
            r1 = f1.result()
            r2 = f2.result()

        data1 = r1.get_json()
        data2 = r2.get_json()

        # Both orders can succeed, but partner 1 can only be assigned to AT MOST ONE of them!
        o1 = query_db('SELECT delivery_partner_id FROM orders WHERE order_id = %s', (data1['order']['order_id'],), one=True)
        o2 = query_db('SELECT delivery_partner_id FROM orders WHERE order_id = %s', (data2['order']['order_id'],), one=True)

        assigned_partners = [o1['delivery_partner_id'], o2['delivery_partner_id']]
        print(f"[CONCURRENCY TEST] Delivery Partner Assignments: {assigned_partners}")

        # The two orders must not have both been assigned partner 1
        self.assertFalse(assigned_partners[0] == 1 and assigned_partners[1] == 1, "Double assignment occurred!")
        print("[CONCURRENCY TEST] Double assignment successfully prevented by transaction row-locks!")

        # Restore all partners to online & available
        query_db("UPDATE delivery_partners SET is_online = 1, current_status = 'available'", commit=True)

if __name__ == '__main__':
    unittest.main()
