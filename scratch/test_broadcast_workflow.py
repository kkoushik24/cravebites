import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def run_test():
    session = requests.Session()
    
    print("\n--- 1. Login Customer ---")
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "customer@dabba.com", "password": "password123"})
    assert r.status_code == 200, f"Customer login failed: {r.text}"
    cust_data = r.json()
    cust_token = cust_data["token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("Customer logged in successfully.")

    print("\n--- 2. Login Restaurant ---")
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "restaurant@dabba.com", "password": "password123"})
    assert r.status_code == 200, f"Restaurant login failed: {r.text}"
    rest_data = r.json()
    rest_token = rest_data["token"]
    rest_headers = {"Authorization": f"Bearer {rest_token}"}
    print("Restaurant logged in successfully.")

    print("\n--- 3. Login Delivery Partner 1 (Ravi) ---")
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "delivery@dabba.com", "password": "password123"})
    assert r.status_code == 200, f"Ravi login failed: {r.text}"
    p1_data = r.json()
    p1_token = p1_data["token"]
    p1_headers = {"Authorization": f"Bearer {p1_token}"}
    print(f"Partner 1 logged in: {p1_data['user']['full_name']} (ID: {p1_data['user'].get('entity_id')})")

    print("\n--- 4. Login Delivery Partner 2 (Suresh) ---")
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": "suresh@dabba.com", "password": "password123"})
    assert r.status_code == 200, f"Suresh login failed: {r.text}"
    p2_data = r.json()
    p2_token = p2_data["token"]
    p2_headers = {"Authorization": f"Bearer {p2_token}"}
    print(f"Partner 2 logged in: {p2_data['user']['full_name']} (ID: {p2_data['user'].get('entity_id')})")

    print("\n--- 5. Reset Delivery Partners to Online & Available ---")
    sys.path.append('food-ordering-system/backend')
    from db import query_db
    query_db("UPDATE orders SET order_status = 'Cancelled' WHERE order_status NOT IN ('Delivered', 'Cancelled')", commit=True)
    query_db("DELETE FROM delivery_rejections", commit=True)
    query_db("UPDATE delivery_partners SET is_online = 1, current_status = 'available'", commit=True)
    print("Partners 1 & 2 reset to online and available, cleaned up old test orders.")

    print("\n--- 6. Place New Order by Customer ---")
    order_payload = {
        "restaurant_id": 1,
        "items": [
            {"item_id": 2, "quantity": 1}
        ],
        "payment_method": "upi",
        "special_instructions": "Multi-rider broadcast test"
    }
    r = session.post(f"{BASE_URL}/api/customer/order", json=order_payload, headers=cust_headers)
    assert r.status_code in (200, 201), f"Order placement failed: {r.text}"
    order_res = r.json()
    order_id = order_res.get("order_id") or order_res.get("order", {}).get("order_id")
    print(f"Order #{order_id} placed successfully.")

    print("\n--- 7. Verify Customer Live Order (Initially Unassigned) ---")
    r = session.get(f"{BASE_URL}/api/customer/order/{order_id}/status", headers=cust_headers)
    assert r.status_code == 200
    live = r.json().get("order")
    assert live is not None, "No live order found"
    assert live["order_id"] == order_id
    assert live.get("delivery_partner_id") is None, f"Expected None delivery_partner_id, got {live.get('delivery_partner_id')}"
    assert live.get("has_rider") is False, f"Expected has_rider False, got {live.get('has_rider')}"
    print(f"Customer view: status={live['order_status']}, has_rider={live['has_rider']}, ETA={live.get('estimated_delivery_minutes')}m")

    print("\n--- 8. Restaurant Accepts Order -> Status Preparing ---")
    r = session.post(f"{BASE_URL}/api/restaurant/order/{order_id}/action", json={"action": "accept"}, headers=rest_headers)
    assert r.status_code == 200, f"Restaurant accept failed: {r.text}"
    
    r = session.get(f"{BASE_URL}/api/restaurant/dashboard", headers=rest_headers)
    assert r.status_code == 200
    preparing = r.json().get("columns", {}).get("preparing", [])
    matched = [o for o in preparing if o["order_id"] == order_id]
    assert len(matched) == 1, f"Order #{order_id} not found in restaurant preparing column"
    rest_order = matched[0]
    assert rest_order["order_status"] == "Preparing"
    assert rest_order.get("delivery_partner_id") is None, f"Restaurant should NOT have assigned rider yet: {rest_order.get('delivery_partner_id')}"
    print(f"Restaurant view: status=Preparing, rider_id={rest_order.get('delivery_partner_id')}, rejections_count={rest_order.get('rejections_count')}")

    print("\n--- 9. Both Partners Check Dashboard (Pending Request Broadcast) ---")
    r1 = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p1_headers).json()
    r2 = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p2_headers).json()
    
    p1_pending = r1.get("pending_request")
    p2_pending = r2.get("pending_request")
    assert p1_pending is not None, f"Partner 1 should see pending request! Got: {r1}"
    assert p1_pending["order_id"] == order_id, f"Partner 1 pending order mismatch: {p1_pending['order_id']}"
    assert p2_pending is not None, f"Partner 2 should see pending request! Got: {r2}"
    assert p2_pending["order_id"] == order_id, f"Partner 2 pending order mismatch: {p2_pending['order_id']}"
    print(f"Partner 1 sees broadcast request for #{order_id}")
    print(f"Partner 2 sees broadcast request for #{order_id}")

    print("\n--- 10. Partner 1 (Ravi) REJECTS the Request ---")
    r = session.post(f"{BASE_URL}/api/delivery/order/{order_id}/reject", json={"reason": "Too far away"}, headers=p1_headers)
    assert r.status_code == 200, f"Reject failed: {r.text}"
    print("Partner 1 rejected request successfully.")

    print("\n--- 11. Check Partner 1 Dashboard (Request Dismissed) ---")
    r1_after = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p1_headers).json()
    assert r1_after.get("pending_request") is None, f"Partner 1 should NO LONGER see pending request! Got: {r1_after.get('pending_request')}"
    print("Partner 1 dashboard is clear (no pending request).")

    print("\n--- 12. Check Restaurant Dashboard (Declined Count = 1, Rider Still Unassigned) ---")
    r = session.get(f"{BASE_URL}/api/restaurant/dashboard", headers=rest_headers)
    preparing = r.json().get("columns", {}).get("preparing", [])
    rest_order = [o for o in preparing if o["order_id"] == order_id][0]
    assert rest_order.get("delivery_partner_id") is None, f"Rider should still be unassigned, got {rest_order.get('delivery_partner_id')}"
    assert rest_order.get("rejections_count") == 1, f"Expected rejections_count 1, got {rest_order.get('rejections_count')}"
    print(f"Restaurant view: rider=None, rejections_count={rest_order.get('rejections_count')} -> CORRECT!")

    print("\n--- 13. Partner 2 (Suresh) STILL sees the Request ---")
    r2_after = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p2_headers).json()
    assert r2_after.get("pending_request") is not None, "Partner 2 must STILL see the pending request after Partner 1 rejected!"
    assert r2_after["pending_request"]["order_id"] == order_id
    print("Partner 2 still sees the pending request -> Broadcast pool is functioning perfectly!")

    print("\n--- 14. Partner 2 (Suresh) ACCEPTS the Request ---")
    r = session.post(f"{BASE_URL}/api/delivery/order/{order_id}/accept", json={}, headers=p2_headers)
    assert r.status_code == 200, f"Accept failed: {r.text}"
    print("Partner 2 accepted request successfully.")

    print("\n--- 15. Verify Partner 2 Active Delivery & Cooking Lock ---")
    r2_active = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p2_headers).json()
    active = r2_active.get("active_delivery")
    assert active is not None, "Partner 2 should have active_delivery!"
    assert active["order_id"] == order_id
    assert active["can_pickup"] is False, f"can_pickup should be False while Preparing! Got: {active['can_pickup']}"
    assert "preparing" in active["status_message"].lower() or "prepared" in active["status_message"].lower() or "cooking" in active["status_message"].lower(), f"Unexpected status message: {active['status_message']}"
    print(f"Partner 2 active delivery: can_pickup={active['can_pickup']}, headline='{active.get('status_headline')}', msg='{active.get('status_message')}'")

    print("\n--- 16. Verify Partner 2 Cannot Pickup While Food is Preparing ---")
    r = session.post(f"{BASE_URL}/api/delivery/order/{order_id}/pickup", json={}, headers=p2_headers)
    assert r.status_code == 400, f"Pickup should fail with 400 when Preparing! Got status {r.status_code}: {r.text}"
    print(f"Cooking lock confirmed: Pickup rejected with 400 -> {r.json().get('error')}")

    print("\n--- 17. Verify Restaurant Shows Suresh Patel Assigned ---")
    r = session.get(f"{BASE_URL}/api/restaurant/dashboard", headers=rest_headers)
    preparing = r.json().get("columns", {}).get("preparing", [])
    rest_order = [o for o in preparing if o["order_id"] == order_id][0]
    assert rest_order.get("partner_name") == "Suresh Patel", f"Expected Suresh Patel, got {rest_order.get('partner_name')}"
    print(f"Restaurant shows assigned rider: {rest_order.get('partner_name')} ({rest_order.get('partner_phone')}) -> CORRECT!")

    print("\n--- 18. Verify Customer App Shows Suresh Patel Assigned ---")
    r = session.get(f"{BASE_URL}/api/customer/order/{order_id}/status", headers=cust_headers)
    live = r.json().get("order")
    assert live["has_rider"] is True, f"Expected has_rider True, got {live['has_rider']}"
    assert live.get("partner_name") == "Suresh Patel", f"Expected Suresh Patel, got {live.get('partner_name')}"
    print(f"Customer shows assigned rider: {live['partner_name']} -> CORRECT!")

    print("\n--- 19. Restaurant Marks Food READY ---")
    r = session.post(f"{BASE_URL}/api/restaurant/order/{order_id}/action", json={"action": "mark_ready"}, headers=rest_headers)
    assert r.status_code == 200, f"Mark ready failed: {r.text}"
    print("Restaurant marked food Ready.")

    print("\n--- 20. Partner 2 Can Now Pick Up ---")
    r2_active = session.get(f"{BASE_URL}/api/delivery/dashboard", headers=p2_headers).json()
    active = r2_active.get("active_delivery")
    assert active["can_pickup"] is True, f"can_pickup should now be True! Got: {active['can_pickup']}"
    
    r = session.post(f"{BASE_URL}/api/delivery/order/{order_id}/pickup", json={}, headers=p2_headers)
    assert r.status_code == 200, f"Pickup failed: {r.text}"
    print("Partner 2 successfully picked up order.")

    print("\n--- 21. Partner 2 Delivers Order ---")
    r = session.post(f"{BASE_URL}/api/delivery/order/{order_id}/drop", json={}, headers=p2_headers)
    assert r.status_code == 200, f"Delivery confirmation failed: {r.text}"
    print("Partner 2 successfully marked order Delivered.")

    print("\n--- 22. Verify Final Customer State ---")
    r = session.get(f"{BASE_URL}/api/customer/order/{order_id}/status", headers=cust_headers)
    live = r.json().get("order")
    assert live.get("order_status") == "Delivered", f"Expected order Delivered, got: {live.get('order_status')}"
    print("Final state verified: Order complete!")

    print("\n==========================================")
    print("ALL 22 STEPS PASSED SUCCESSFULLY! 🎯")
    print("==========================================\n")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
