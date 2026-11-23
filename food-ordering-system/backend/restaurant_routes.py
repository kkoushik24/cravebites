"""
Restaurant kitchen dashboard routes and REST JSON APIs.
Live order dispatching (New, Preparing, Ready), menu management, stock switches,
today's sales statistics, and orders-by-hour telemetry.
"""

from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, request, jsonify, render_template, session
from auth import login_required
from db import query_db, call_procedure

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('/restaurant')
@restaurant_bp.route('/restaurant/')
@login_required('restaurant')
def restaurant_home():
    return render_template('restaurant/index.html')


@restaurant_bp.route('/api/restaurant/dashboard', methods=['GET'])
@login_required('restaurant')
def get_restaurant_dashboard():
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    # 1. Restaurant Profile
    restaurant = query_db('''
        SELECT restaurant_id, name, tagline, cuisine_type, rating, total_ratings,
               prep_time_min, is_accepting_orders, address, phone
        FROM restaurants
        WHERE restaurant_id = %s
    ''', (restaurant_id,), one=True)
    if not restaurant:
        return jsonify({'success': False, 'error': 'Restaurant record not found.'}), 404

    restaurant['rating'] = float(restaurant['rating'])

    # 2. Key Performance Indicators (Today)
    kpis = query_db('''
        SELECT 
            COUNT(order_id) AS orders_today,
            COALESCE(SUM(CASE WHEN order_status = 'Delivered' THEN total_amount ELSE 0 END), 0.00) AS revenue_today,
            COALESCE(AVG(CASE WHEN order_status = 'Delivered' THEN total_amount ELSE NULL END), 0.00) AS avg_order_val,
            COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_today
        FROM orders
        WHERE restaurant_id = %s AND DATE(placed_at) = CURRENT_DATE()
    ''', (restaurant_id,), one=True)

    orders_today_count = kpis['orders_today'] if kpis else 0
    revenue_today_amount = float(kpis['revenue_today']) if kpis else 0.0
    avg_order_value = float(kpis['avg_order_val']) if kpis else 0.0

    # Reviews today
    rev_today = query_db('''
        SELECT COALESCE(AVG(restaurant_rating), 4.6) AS rating_today, COUNT(*) AS reviews_count
        FROM reviews
        WHERE restaurant_id = %s AND DATE(created_at) = CURRENT_DATE()
    ''', (restaurant_id,), one=True)
    rating_today_val = float(rev_today['rating_today']) if rev_today and rev_today['reviews_count'] > 0 else float(restaurant['rating'])
    reviews_count = rev_today['reviews_count'] if rev_today else 0

    # 3. Live Orders partitioned into columns: New, Preparing, Ready
    live_orders_raw = query_db('''
        SELECT o.order_id, o.customer_id, u.full_name AS customer_name, u.phone AS customer_phone,
               o.order_status, o.total_amount, o.subtotal, o.delivery_fee, o.placed_at,
               o.accepted_at, o.ready_at, o.estimated_delivery_minutes,
               p.payment_method, p.payment_status,
               o.delivery_partner_id,
               dp.partner_id, u_dp.full_name AS partner_name, u_dp.phone AS partner_phone,
               dp.vehicle_type, dp.vehicle_number, dp.rating AS partner_rating,
               del.distance_km, del.status AS delivery_status,
               TIMESTAMPDIFF(MINUTE, o.placed_at, NOW()) AS minutes_ago,
               (SELECT COUNT(*) FROM delivery_rejections WHERE order_id = o.order_id) AS rejections_count
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN users u ON c.user_id = u.user_id
        JOIN payments p ON o.order_id = p.order_id
        LEFT JOIN deliveries del ON o.order_id = del.order_id
        LEFT JOIN delivery_partners dp ON o.delivery_partner_id = dp.partner_id
        LEFT JOIN users u_dp ON dp.user_id = u_dp.user_id
        WHERE o.restaurant_id = %s AND o.order_status IN ('Placed', 'Accepted', 'Preparing', 'Ready')
        ORDER BY o.placed_at ASC
    ''', (restaurant_id,))

    new_orders = []
    preparing_orders = []
    ready_orders = []

    for o in live_orders_raw:
        o['total_amount'] = float(o['total_amount'])
        o['subtotal'] = float(o['subtotal'])
        o['placed_at'] = o['placed_at'].isoformat() if o['placed_at'] else None
        o['accepted_at'] = o['accepted_at'].isoformat() if o['accepted_at'] else None
        o['ready_at'] = o['ready_at'].isoformat() if o['ready_at'] else None

        # Fetch items summary string (e.g. "1 Chicken Dum Biryani, 2 Raita")
        items = query_db('SELECT item_name, quantity FROM order_items WHERE order_id = %s', (o['order_id'],))
        items_summary = ', '.join([f"{it['quantity']} {it['item_name']}" for it in items])
        o['items_summary'] = items_summary
        o['items_count'] = sum(it['quantity'] for it in items)

        status = o['order_status']
        if status == 'Placed':
            new_orders.append(o)
        elif status in ('Accepted', 'Preparing'):
            preparing_orders.append(o)
        elif status == 'Ready':
            ready_orders.append(o)

    # 4. Real Orders By Hour (5 PM to 12 AM: hours 17, 18, 19, 20, 21, 22, 23, 0)
    hourly_counts = query_db('''
        SELECT HOUR(placed_at) AS hr, COUNT(*) AS count
        FROM orders
        WHERE restaurant_id = %s AND DATE(placed_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY HOUR(placed_at)
    ''', (restaurant_id,))
    hour_map = {row['hr']: row['count'] for row in hourly_counts}

    target_hours = [17, 18, 19, 20, 21, 22, 23, 0]
    chart_bars = []
    max_h = max(hour_map.values()) if hour_map else 1
    if max_h == 0:
        max_h = 1

    for h in target_hours:
        cnt = hour_map.get(h, 0)
        # Calculate height from 20px to 110px
        h_px = int(24 + (cnt / max_h) * 86) if cnt > 0 else 24
        chart_bars.append({
            'hour_label': f"{h-12 if h > 12 else (12 if h == 0 else h)} {'pm' if 12 <= h < 24 else 'am'}",
            'count': cnt,
            'height_px': h_px,
            'is_peak': (cnt == max_h and cnt > 0)
        })

    # 5. Running Low Inventory items (< 10 left or unavailable)
    running_low = query_db('''
        SELECT item_id, name, stock_quantity, is_available
        FROM menu_items
        WHERE restaurant_id = %s AND (stock_quantity <= 10 OR is_available = 0)
        ORDER BY is_available ASC, stock_quantity ASC
        LIMIT 6
    ''', (restaurant_id,))

    return jsonify({
        'success': True,
        'restaurant': restaurant,
        'stats': {
            'orders_today': orders_today_count,
            'revenue_today': revenue_today_amount,
            'avg_order_value': avg_order_value,
            'prep_time_min': restaurant['prep_time_min'],
            'rating_today': rating_today_val,
            'reviews_count': reviews_count
        },
        'columns': {
            'new': new_orders,
            'preparing': preparing_orders,
            'ready': ready_orders
        },
        'chart_bars': chart_bars,
        'running_low': running_low
    })


@restaurant_bp.route('/api/restaurant/status', methods=['POST'])
@login_required('restaurant')
def toggle_restaurant_status():
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    data = request.get_json() or {}
    accepting = 1 if data.get('is_accepting_orders') else 0

    query_db('UPDATE restaurants SET is_accepting_orders = %s WHERE restaurant_id = %s', (accepting, restaurant_id), commit=True)
    return jsonify({
        'success': True,
        'is_accepting_orders': accepting,
        'message': 'Kitchen status updated successfully.'
    })


@restaurant_bp.route('/api/restaurant/order/<int:order_id>/action', methods=['POST'])
@login_required('restaurant')
def perform_order_action(order_id):
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    user_id = getattr(request, 'user_id', None) or session.get('user_id')
    data = request.get_json() or {}
    action = data.get('action', '').strip().lower()

    order = query_db('SELECT order_id, order_status, delivery_partner_id FROM orders WHERE order_id = %s AND restaurant_id = %s', (order_id, restaurant_id), one=True)
    if not order:
        return jsonify({'success': False, 'error': 'Order not found.'}), 404

    current_status = order['order_status']

    if action == 'accept':
        if current_status != 'Placed':
            return jsonify({'success': False, 'error': f'Cannot accept order with status {current_status}.'}), 400
        # Transition to Preparing with no rider locked
        query_db('''
            UPDATE orders 
            SET order_status = 'Preparing', accepted_at = NOW(), delivery_partner_id = NULL
            WHERE order_id = %s
        ''', (order_id,), commit=True)

        # Clear any previous rejections for this order
        query_db('DELETE FROM delivery_rejections WHERE order_id = %s', (order_id,), commit=True)

        return jsonify({
            'success': True,
            'message': 'Order accepted and marked as Preparing! Delivery request broadcasted to all online riders.'
        })

    elif action == 'request_rider':
        if current_status not in ('Accepted', 'Preparing', 'Ready'):
            return jsonify({'success': False, 'error': f'Cannot request rider for order in {current_status} status.'}), 400

        # Reset rejections and clear any unassigned delivery rows so all riders receive the broadcast
        query_db('DELETE FROM delivery_rejections WHERE order_id = %s', (order_id,), commit=True)
        query_db('UPDATE orders SET delivery_partner_id = NULL WHERE order_id = %s', (order_id,), commit=True)
        query_db("DELETE FROM deliveries WHERE order_id = %s AND status IN ('requested', 'rejected')", (order_id,), commit=True)

        return jsonify({'success': True, 'message': 'Pickup request broadcasted to all online delivery partners!'})

    elif action == 'reject':
        if current_status != 'Placed':
            return jsonify({'success': False, 'error': f'Cannot reject order with status {current_status}.'}), 400
        # Call cancel_order stored procedure to restore inventory & refund
        args = [order_id, user_id, 'Restaurant rejected order: Kitchen capacity full', 0, '']
        res = call_procedure('cancel_order', args)
        return jsonify({'success': True, 'message': 'Order rejected and customer notified.'})

    elif action == 'mark_ready':
        if current_status not in ('Accepted', 'Preparing'):
            return jsonify({'success': False, 'error': f'Cannot mark ready from status {current_status}.'}), 400
        query_db('''
            UPDATE orders
            SET order_status = 'Ready', ready_at = NOW()
            WHERE order_id = %s
        ''', (order_id,), commit=True)
        return jsonify({'success': True, 'message': 'Order is marked Ready for pickup!'})

    elif action == 'hand_over':
        if current_status != 'Ready':
            return jsonify({'success': False, 'error': 'Order must be Ready before handing over to rider.'}), 400
        query_db('''
            UPDATE orders
            SET order_status = 'Picked up', picked_at = NOW()
            WHERE order_id = %s
        ''', (order_id,), commit=True)
        query_db('''
            UPDATE deliveries
            SET status = 'picked_up', pickup_time = NOW()
            WHERE order_id = %s
        ''', (order_id,), commit=True)
        return jsonify({'success': True, 'message': 'Order handed over to delivery partner.'})

    return jsonify({'success': False, 'error': 'Invalid action.'}), 400


@restaurant_bp.route('/api/restaurant/menu', methods=['GET', 'POST'])
@login_required('restaurant')
def manage_menu():
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    if request.method == 'GET':
        items = query_db('''
            SELECT m.item_id, m.category_id, c.name AS category_name, m.name, m.description,
                   m.price, m.is_veg, m.is_available, m.stock_quantity, m.image_letter,
                   m.badge_bg, m.badge_text
            FROM menu_items m
            JOIN categories c ON m.category_id = c.category_id
            WHERE m.restaurant_id = %s
            ORDER BY c.display_order ASC, m.item_id ASC
        ''', (restaurant_id,))
        for it in items:
            it['price'] = float(it['price'])
        return jsonify({'success': True, 'menu_items': items})

    # POST: Add new menu item
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    category_id = int(data.get('category_id', 1))
    price = float(data.get('price', 0.0))
    is_veg = 1 if data.get('is_veg') else 0
    stock_quantity = int(data.get('stock_quantity', 50))
    description = data.get('description', '').strip()
    image_letter = (name[0] if name else 'D').upper()

    if not name or price <= 0:
        return jsonify({'success': False, 'error': 'Valid dish name and price are required.'}), 400

    res = query_db('''
        INSERT INTO menu_items (restaurant_id, category_id, name, description, price, is_veg, is_available, stock_quantity, image_letter)
        VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
    ''', (restaurant_id, category_id, name, description, price, is_veg, stock_quantity, image_letter), commit=True)

    return jsonify({'success': True, 'message': 'Dish added to menu.', 'item_id': res['lastrowid']}), 201


@restaurant_bp.route('/api/restaurant/menu/<int:item_id>/toggle-stock', methods=['POST'])
@login_required('restaurant')
def toggle_menu_item_stock(item_id):
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    item = query_db('SELECT item_id, is_available, stock_quantity FROM menu_items WHERE item_id = %s AND restaurant_id = %s', (item_id, restaurant_id), one=True)
    if not item:
        return jsonify({'success': False, 'error': 'Menu item not found.'}), 404

    new_avail = 0 if item['is_available'] == 1 else 1
    new_stock = item['stock_quantity']
    if new_avail == 1 and new_stock == 0:
        new_stock = 20

    query_db('UPDATE menu_items SET is_available = %s, stock_quantity = %s WHERE item_id = %s', (new_avail, new_stock, item_id), commit=True)

    return jsonify({
        'success': True,
        'item_id': item_id,
        'is_available': new_avail,
        'stock_quantity': new_stock,
        'message': f"Item is now {'available' if new_avail else 'sold out'}."
    })


@restaurant_bp.route('/api/restaurant/reports/monthly', methods=['GET'])
@login_required('restaurant')
def get_monthly_report():
    restaurant_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    now = datetime.now()
    year = request.args.get('year', now.year, type=int)
    month = request.args.get('month', now.month, type=int)

    # Call monthly_sales_report stored procedure
    conn = query_db
    result = query_db('''
        SELECT 
            r.restaurant_id,
            r.name AS restaurant_name,
            COUNT(o.order_id) AS total_orders,
            COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS delivered_orders,
            COUNT(CASE WHEN o.order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
            COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.subtotal ELSE 0 END), 0.00) AS gross_sales,
            COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE 0 END), 0.00) AS net_revenue,
            COALESCE(AVG(CASE WHEN o.order_status = 'Delivered' THEN o.total_amount ELSE NULL END), 0.00) AS avg_ticket
        FROM restaurants r
        LEFT JOIN orders o ON r.restaurant_id = o.restaurant_id
            AND YEAR(o.placed_at) = %s AND MONTH(o.placed_at) = %s
        WHERE r.restaurant_id = %s
        GROUP BY r.restaurant_id, r.name
    ''', (year, month, restaurant_id), one=True)

    if result:
        result['gross_sales'] = float(result['gross_sales'])
        result['net_revenue'] = float(result['net_revenue'])
        result['avg_ticket'] = float(result['avg_ticket'])

    return jsonify({'success': True, 'report': result})

