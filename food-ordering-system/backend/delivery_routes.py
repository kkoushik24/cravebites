"""
Delivery partner routes and REST JSON APIs.
Mobile rider interface matching design/dabba-delivery.html:
Online/offline toggle, auto-assigned order delivery flow (pickup -> drop),
slide-to-confirm interaction, and daily payout & trip telemetry.
"""

from decimal import Decimal
from flask import Blueprint, request, jsonify, render_template, session
from auth import login_required
from db import query_db

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/delivery')
@delivery_bp.route('/delivery/')
@login_required('delivery_partner')
def delivery_home():
    return render_template('delivery/index.html')


@delivery_bp.route('/api/delivery/dashboard', methods=['GET'])
@login_required('delivery_partner')
def get_delivery_dashboard():
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    # 1. Partner Details
    partner = query_db('''
        SELECT dp.partner_id, u.full_name, u.phone, dp.vehicle_type, dp.vehicle_number,
               dp.is_online, dp.current_status, dp.total_trips, dp.total_earnings,
               dp.hours_online, dp.rating
        FROM delivery_partners dp
        JOIN users u ON dp.user_id = u.user_id
        WHERE dp.partner_id = %s
    ''', (partner_id,), one=True)

    if not partner:
        return jsonify({'success': False, 'error': 'Delivery partner record not found.'}), 404

    partner['total_earnings'] = float(partner['total_earnings'])
    partner['hours_online'] = float(partner['hours_online'])
    partner['rating'] = float(partner['rating'])

    # 2. Today's Trips & Earnings Calculation
    today_stats = query_db('''
        SELECT 
            COUNT(d.delivery_id) AS trips_today,
            COALESCE(SUM(d.delivery_fee_earned), 0.00) AS earnings_today
        FROM deliveries d
        WHERE d.partner_id = %s 
          AND d.status = 'delivered'
          AND DATE(d.delivery_time) = CURRENT_DATE()
    ''', (partner_id,), one=True)

    trips_today = today_stats['trips_today'] if today_stats and today_stats['trips_today'] > 0 else partner['total_trips']
    earnings_today = float(today_stats['earnings_today']) if today_stats and today_stats['earnings_today'] > 0 else float(partner['total_earnings'])

    # 3. Pending Pickup Request (broadcasted to all online available partners until claimed)
    pending_request = None
    if partner['is_online'] == 1 and partner['current_status'] == 'available':
        pending_order = query_db('''
            SELECT o.order_id, o.order_status, o.placed_at, o.special_instructions,
                   r.name AS restaurant_name, r.address AS restaurant_address, r.phone AS restaurant_phone,
                   u_cust.full_name AS customer_name, u_cust.phone AS customer_phone,
                   addr.label AS address_label, addr.address_line AS drop_address, addr.landmark, addr.city,
                   3.2 AS distance_km, 50.00 AS delivery_fee_earned
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.restaurant_id
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u_cust ON c.user_id = u_cust.user_id
            JOIN addresses addr ON o.address_id = addr.address_id
            WHERE o.order_status IN ('Preparing', 'Ready')
              AND o.delivery_partner_id IS NULL
              AND o.placed_at >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
              AND o.order_id NOT IN (
                  SELECT order_id FROM delivery_rejections WHERE partner_id = %s
              )
            ORDER BY o.placed_at DESC
            LIMIT 1
        ''', (partner_id,), one=True)

        if pending_order:
            pending_order['distance_km'] = float(pending_order['distance_km'])
            pending_order['delivery_fee_earned'] = float(pending_order['delivery_fee_earned'])
            req_items = query_db('SELECT item_name, quantity FROM order_items WHERE order_id = %s', (pending_order['order_id'],))
            pending_order['items_count'] = sum(it['quantity'] for it in req_items)
            pending_order['items_summary'] = ', '.join([f"{it['quantity']} {it['item_name']}" for it in req_items])
            pending_request = pending_order

    # 4. Active Delivery Task (strictly assigned to this partner)
    active_delivery = query_db('''
        SELECT d.delivery_id, d.order_id, d.partner_id, d.status AS delivery_status,
               d.distance_km, d.delivery_fee_earned,
               o.order_status, o.placed_at, o.accepted_at, o.ready_at, o.picked_at, o.special_instructions,
               r.name AS restaurant_name, r.address AS restaurant_address, r.phone AS restaurant_phone, r.prep_time_min,
               u_cust.full_name AS customer_name, u_cust.phone AS customer_phone,
               addr.label AS address_label, addr.address_line AS drop_address, addr.landmark, addr.city,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.accepted_at, o.placed_at), NOW()) AS elapsed_prep_min,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.picked_at, NOW()), NOW()) AS elapsed_transit_min
        FROM orders o
        JOIN deliveries d ON o.order_id = d.order_id
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN users u_cust ON c.user_id = u_cust.user_id
        JOIN addresses addr ON o.address_id = addr.address_id
        WHERE o.delivery_partner_id = %s
          AND d.status IN ('assigned', 'picked_up')
          AND o.order_status NOT IN ('Cancelled', 'Delivered', 'Rejected')
        ORDER BY d.created_at DESC
        LIMIT 1
    ''', (partner_id,), one=True)

    if active_delivery:
        active_delivery['distance_km'] = float(active_delivery['distance_km'])
        active_delivery['delivery_fee_earned'] = float(active_delivery['delivery_fee_earned'])

        # Fetch items count and summary
        items = query_db('SELECT item_name, quantity FROM order_items WHERE order_id = %s', (active_delivery['order_id'],))
        active_delivery['items_count'] = sum(it['quantity'] for it in items)
        active_delivery['items_summary'] = ', '.join([f"{it['quantity']} {it['item_name']}" for it in items])

        # Dynamic ETA calculations
        order_st = active_delivery['order_status']
        prep_min = active_delivery.get('prep_time_min') or 20
        elapsed_prep = active_delivery.get('elapsed_prep_min') or 0
        remaining_prep = max(2, prep_min - elapsed_prep)

        if order_st in ('Placed', 'Accepted', 'Preparing'):
            active_delivery['can_pickup'] = False
            active_delivery['remaining_prep_min'] = remaining_prep
            active_delivery['total_eta_min'] = remaining_prep + 12
            active_delivery['kpi_pickup_time'] = f"Cooking (~{remaining_prep}m)"
            active_delivery['kpi_total_time'] = f"{remaining_prep + 12} min"
            active_delivery['status_headline'] = 'Kitchen is cooking'
            active_delivery['status_message'] = f"Food is being prepared at {active_delivery['restaurant_name']}. Ready in ~{remaining_prep} min."
        elif order_st == 'Ready':
            active_delivery['can_pickup'] = True
            active_delivery['remaining_prep_min'] = 0
            active_delivery['total_eta_min'] = 12
            active_delivery['kpi_pickup_time'] = "Ready now!"
            active_delivery['kpi_total_time'] = "12 min"
            active_delivery['status_headline'] = 'Ready for pickup!'
            active_delivery['status_message'] = "Order is ready at the restaurant counter. Pick up and confirm."
        elif order_st == 'Picked up':
            active_delivery['can_pickup'] = False
            elapsed_transit = active_delivery.get('elapsed_transit_min') or 0
            remaining_transit = max(2, 12 - elapsed_transit)
            active_delivery['remaining_transit_min'] = remaining_transit
            active_delivery['total_eta_min'] = remaining_transit
            active_delivery['kpi_pickup_time'] = "Done"
            active_delivery['kpi_total_time'] = f"{remaining_transit} min"
            active_delivery['status_headline'] = 'En route to customer'
            active_delivery['status_message'] = f"Deliver to {active_delivery['customer_name']} at {active_delivery['drop_address']}."
        else:
            active_delivery['can_pickup'] = False
            active_delivery['total_eta_min'] = 0
            active_delivery['kpi_pickup_time'] = '-'
            active_delivery['kpi_total_time'] = '-'

    return jsonify({
        'success': True,
        'partner': partner,
        'trips_today': trips_today,
        'earnings_today': earnings_today,
        'pending_request': pending_request,
        'active_delivery': active_delivery
    })


@delivery_bp.route('/api/delivery/status', methods=['POST'])
@login_required('delivery_partner')
def toggle_delivery_status():
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    data = request.get_json() or {}
    is_online = 1 if data.get('is_online') else 0

    partner = query_db('SELECT current_status FROM delivery_partners WHERE partner_id = %s', (partner_id,), one=True)
    new_status = 'offline' if not is_online else ('busy' if partner['current_status'] == 'busy' else 'available')

    query_db('''
        UPDATE delivery_partners
        SET is_online = %s, current_status = %s
        WHERE partner_id = %s
    ''', (is_online, new_status, partner_id), commit=True)

    return jsonify({
        'success': True,
        'is_online': is_online,
        'current_status': new_status,
        'message': f"You are now {'online' if is_online else 'offline'}."
    })


@delivery_bp.route('/api/delivery/order/<int:order_id>/accept', methods=['POST'])
@login_required('delivery_partner')
def accept_delivery_request(order_id):
    """Triggered when rider taps ACCEPT on a new pickup request modal."""
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    # 1. Check order status & verify it is not already claimed by someone else
    order = query_db('SELECT order_id, order_status, delivery_partner_id FROM orders WHERE order_id = %s', (order_id,), one=True)
    if not order:
        return jsonify({'success': False, 'error': 'Order not found.'}), 404

    if order['order_status'] not in ('Preparing', 'Ready'):
        return jsonify({'success': False, 'error': f"Order is in '{order['order_status']}' status and not available for pickup."}), 400

    if order['delivery_partner_id'] is not None and order['delivery_partner_id'] != partner_id:
        return jsonify({'success': False, 'error': 'This order was already accepted by another delivery partner!'}), 409

    # 2. Atomically claim order for this partner
    query_db('''
        UPDATE orders
        SET delivery_partner_id = %s
        WHERE order_id = %s AND (delivery_partner_id IS NULL OR delivery_partner_id = %s)
    ''', (partner_id, order_id, partner_id), commit=True)

    # Verify claim succeeded
    check = query_db('SELECT delivery_partner_id FROM orders WHERE order_id = %s', (order_id,), one=True)
    if not check or check['delivery_partner_id'] != partner_id:
        return jsonify({'success': False, 'error': 'This order was just accepted by another delivery partner!'}), 409

    # 3. Insert or update delivery record
    query_db('''
        INSERT INTO deliveries (order_id, partner_id, distance_km, delivery_fee_earned, status, created_at)
        VALUES (%s, %s, 3.2, 50.00, 'assigned', NOW())
        ON DUPLICATE KEY UPDATE partner_id = VALUES(partner_id), status = 'assigned', created_at = NOW()
    ''', (order_id, partner_id), commit=True)

    # 4. Mark this delivery partner as busy
    query_db('''
        UPDATE delivery_partners
        SET current_status = 'busy'
        WHERE partner_id = %s
    ''', (partner_id,), commit=True)

    return jsonify({
        'success': True,
        'status': 'assigned',
        'message': 'Pickup request accepted! Drive to restaurant.'
    })


@delivery_bp.route('/api/delivery/order/<int:order_id>/reject', methods=['POST'])
@login_required('delivery_partner')
def reject_delivery_request(order_id):
    """Triggered when rider taps REJECT on a pickup request modal."""
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    # Record rejection for this specific rider so they don't see this order again
    query_db('''
        INSERT INTO delivery_rejections (order_id, partner_id, created_at)
        VALUES (%s, %s, NOW())
        ON DUPLICATE KEY UPDATE created_at = NOW()
    ''', (order_id, partner_id), commit=True)

    # If this order had a requested/assigned delivery pointing to this partner, clear it
    query_db('''
        UPDATE orders
        SET delivery_partner_id = NULL
        WHERE order_id = %s AND delivery_partner_id = %s
    ''', (order_id, partner_id), commit=True)

    query_db('''
        DELETE FROM deliveries
        WHERE order_id = %s AND partner_id = %s AND status IN ('requested', 'rejected')
    ''', (order_id, partner_id), commit=True)

    # Leave this partner available to receive other orders
    query_db('''
        UPDATE delivery_partners
        SET current_status = 'available'
        WHERE partner_id = %s
    ''', (partner_id,), commit=True)

    return jsonify({
        'success': True,
        'status': 'rejected',
        'message': 'Pickup request declined.'
    })


@delivery_bp.route('/api/delivery/order/<int:order_id>/pickup', methods=['POST'])
@login_required('delivery_partner')
def confirm_pickup(order_id):
    """Triggered by the Slide-to-confirm pickup control in the delivery app."""
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    delivery = query_db('''
        SELECT delivery_id, status FROM deliveries
        WHERE order_id = %s AND partner_id = %s
    ''', (order_id, partner_id), one=True)

    if not delivery:
        return jsonify({'success': False, 'error': 'Delivery assignment not found.'}), 404

    order = query_db('SELECT order_status FROM orders WHERE order_id = %s', (order_id,), one=True)
    if not order:
        return jsonify({'success': False, 'error': 'Order not found.'}), 404

    if order['order_status'] != 'Ready':
        return jsonify({
            'success': False,
            'error': f"Restaurant is still cooking this order ({order['order_status']})! Pickup is only allowed after the food is marked 'Ready'."
        }), 400

    # Update delivery and order status
    query_db('''
        UPDATE deliveries
        SET status = 'picked_up', pickup_time = NOW()
        WHERE delivery_id = %s
    ''', (delivery['delivery_id'],), commit=True)

    query_db('''
        UPDATE orders
        SET order_status = 'Picked up', picked_at = NOW()
        WHERE order_id = %s
    ''', (order_id,), commit=True)

    return jsonify({
        'success': True,
        'status': 'picked_up',
        'message': 'Order picked up! Navigate to the customer address.'
    })


@delivery_bp.route('/api/delivery/order/<int:order_id>/drop', methods=['POST'])
@login_required('delivery_partner')
def confirm_drop(order_id):
    """Triggered by the Slide-to-confirm delivered control in the delivery app."""
    partner_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    delivery = query_db('''
        SELECT delivery_id, delivery_fee_earned FROM deliveries
        WHERE order_id = %s AND partner_id = %s
    ''', (order_id, partner_id), one=True)

    if not delivery:
        return jsonify({'success': False, 'error': 'Delivery assignment not found.'}), 404

    fee = float(delivery['delivery_fee_earned'])

    # 1. Update delivery record
    query_db('''
        UPDATE deliveries
        SET status = 'delivered', delivery_time = NOW()
        WHERE delivery_id = %s
    ''', (delivery['delivery_id'],), commit=True)

    # 2. Update order status to Delivered
    query_db('''
        UPDATE orders
        SET order_status = 'Delivered', delivered_at = NOW()
        WHERE order_id = %s
    ''', (order_id,), commit=True)

    # 3. Update partner metrics & set status to available
    query_db('''
        UPDATE delivery_partners
        SET current_status = 'available',
            total_trips = total_trips + 1,
            total_earnings = total_earnings + %s
        WHERE partner_id = %s
    ''', (fee, partner_id), commit=True)

    return jsonify({
        'success': True,
        'status': 'delivered',
        'fee_earned': fee,
        'message': f'Order delivered! ₹{fee:.2f} credited to your earnings.'
    })

