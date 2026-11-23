"""
Customer routes and REST JSON APIs for browsing, ordering, and live tracking.
All database operations use parameterized queries.
"""

import json
from decimal import Decimal
from datetime import datetime, date
from flask import Blueprint, request, jsonify, render_template, session, redirect
from auth import login_required
from db import query_db, call_procedure

customer_bp = Blueprint('customer', __name__)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError

@customer_bp.route('/customer')
@customer_bp.route('/customer/')
@login_required('customer')
def customer_home():
    return render_template('customer/index.html')


@customer_bp.route('/customer/orders')
@login_required('customer')
def customer_orders_page():
    return render_template('customer/orders.html')


@customer_bp.route('/customer/profile')
@login_required('customer')
def customer_profile_page():
    return render_template('customer/profile.html')


@customer_bp.route('/api/customer/bootstrap', methods=['GET'])
@login_required('customer')
def customer_bootstrap():
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    # 1. Customer profile & default address
    customer = query_db('''
        SELECT c.customer_id, u.full_name, u.email, u.phone, c.loyalty_points
        FROM customers c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.customer_id = %s
    ''', (customer_id,), one=True)

    addresses = query_db('''
        SELECT address_id, label, address_line, landmark, city, postal_code, is_default
        FROM addresses
        WHERE customer_id = %s
        ORDER BY is_default DESC, address_id DESC
    ''', (customer_id,))

    default_address = next((a for a in addresses if a['is_default']), addresses[0] if addresses else None)

    # 2. Categories
    categories = query_db('SELECT category_id, name FROM categories ORDER BY display_order ASC')

    # 3. Tonight's Picks (Carousel dishes)
    carousel_items = query_db('''
        SELECT m.item_id, m.name, m.price, m.image_letter, m.badge_bg, m.badge_text,
               r.restaurant_id, r.name AS restaurant_name
        FROM menu_items m
        JOIN restaurants r ON m.restaurant_id = r.restaurant_id
        WHERE m.item_id IN (1, 13, 32, 5, 10)
        ORDER BY FIELD(m.item_id, 1, 13, 32, 5, 10)
    ''')
    if not carousel_items:
        carousel_items = query_db('''
            SELECT m.item_id, m.name, m.price, m.image_letter, m.badge_bg, m.badge_text,
                   r.restaurant_id, r.name AS restaurant_name
            FROM menu_items m
            JOIN restaurants r ON m.restaurant_id = r.restaurant_id
            WHERE m.is_available = 1
            LIMIT 5
        ''')

    # Convert Decimals
    for item in carousel_items:
        item['price'] = float(item['price'])

    # 4. Active Order for live tracker widget (e.g. Placed, Accepted, Preparing, Ready, Picked up)
    # Only consider orders placed within the last 3 hours to avoid stale tracking cards
    active_order = query_db('''
        SELECT o.order_id, o.order_status, o.total_amount, o.subtotal, o.discount_amount, o.delivery_fee, o.tax_amount,
               o.placed_at, o.accepted_at, o.ready_at, o.picked_at, o.delivered_at, o.cancelled_at,
               o.estimated_delivery_minutes,
               r.restaurant_id, r.name AS restaurant_name, r.prep_time_min,
               o.delivery_partner_id, u_dp.full_name AS partner_name, u_dp.phone AS partner_phone,
               dp.rating AS partner_rating, dp.vehicle_type, dp.vehicle_number,
               del.distance_km, del.status AS delivery_status,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.accepted_at, o.placed_at), NOW()) AS elapsed_prep_min,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.picked_at, NOW()), NOW()) AS elapsed_transit_min
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        LEFT JOIN delivery_partners dp ON o.delivery_partner_id = dp.partner_id
        LEFT JOIN users u_dp ON dp.user_id = u_dp.user_id
        LEFT JOIN deliveries del ON o.order_id = del.order_id
        WHERE o.customer_id = %s 
          AND o.order_status NOT IN ('Delivered', 'Cancelled', 'Rejected')
          AND o.placed_at >= DATE_SUB(NOW(), INTERVAL 3 HOUR)
        ORDER BY o.placed_at DESC
        LIMIT 1
    ''', (customer_id,), one=True)

    if active_order:
        active_order['total_amount'] = float(active_order['total_amount'])
        if active_order.get('distance_km'):
            active_order['distance_km'] = float(active_order['distance_km'])
        for k in ['placed_at', 'accepted_at', 'ready_at', 'picked_at', 'delivered_at', 'cancelled_at']:
            if active_order.get(k):
                active_order[k] = active_order[k].isoformat()

        # Dynamic estimation
        order_st = active_order['order_status']
        prep_min = active_order.get('prep_time_min') or 20
        elapsed_p = active_order.get('elapsed_prep_min') or 0
        rem_prep = max(2, prep_min - elapsed_p)

        if order_st in ('Placed', 'Accepted'):
            active_order['estimated_delivery_minutes'] = prep_min + 12
            active_order['eta_status_text'] = 'Order Confirmed · Preparing soon'
            active_order['step_index'] = 0
        elif order_st == 'Preparing':
            active_order['estimated_delivery_minutes'] = rem_prep + 12
            active_order['eta_status_text'] = f'Kitchen is cooking · ~{rem_prep}m left'
            active_order['step_index'] = 1
        elif order_st == 'Ready':
            active_order['estimated_delivery_minutes'] = 12
            active_order['eta_status_text'] = 'Food is ready · Rider picking up'
            active_order['step_index'] = 1
        elif order_st == 'Picked up':
            elapsed_tr = active_order.get('elapsed_transit_min') or 0
            rem_tr = max(2, 12 - elapsed_tr)
            active_order['estimated_delivery_minutes'] = rem_tr
            active_order['eta_status_text'] = f'Out for delivery · ~{rem_tr}m away'
            active_order['step_index'] = 2
        elif order_st == 'Delivered':
            active_order['estimated_delivery_minutes'] = 0
            active_order['eta_status_text'] = 'Delivered! Enjoy your food'
            active_order['step_index'] = 3

        active_order['has_rider'] = bool(active_order.get('delivery_partner_id') and active_order.get('partner_name'))

    # 5. Restaurants preview
    restaurants = query_db('''
        SELECT restaurant_id, name, tagline, cuisine_type, rating, total_ratings, prep_time_min, is_accepting_orders, address
        FROM restaurants
        ORDER BY rating DESC
    ''')
    for r in restaurants:
        r['rating'] = float(r['rating'])

    return jsonify({
        'success': True,
        'customer': customer,
        'default_address': default_address,
        'addresses': addresses,
        'categories': categories,
        'carousel_items': carousel_items,
        'active_order': active_order,
        'restaurants': restaurants
    })


@customer_bp.route('/api/customer/restaurants', methods=['GET'])
@login_required('customer')
def get_restaurants():
    q = request.args.get('q', '').strip()
    cuisine = request.args.get('cuisine', '').strip()
    min_rating = request.args.get('min_rating', type=float)

    sql = '''
        SELECT restaurant_id, name, tagline, description, cuisine_type, rating, total_ratings,
               prep_time_min, is_accepting_orders, address, phone
        FROM restaurants
        WHERE 1=1
    '''
    params = []

    if q:
        sql += ' AND (name LIKE %s OR cuisine_type LIKE %s OR description LIKE %s)'
        like_q = f'%{q}%'
        params.extend([like_q, like_q, like_q])

    if cuisine:
        sql += ' AND cuisine_type LIKE %s'
        params.append(f'%{cuisine}%')

    if min_rating:
        sql += ' AND rating >= %s'
        params.append(min_rating)

    sql += ' ORDER BY is_accepting_orders DESC, rating DESC'

    restaurants = query_db(sql, tuple(params))
    for r in restaurants:
        r['rating'] = float(r['rating'])

    return jsonify({'success': True, 'restaurants': restaurants})


@customer_bp.route('/api/customer/restaurant/<int:restaurant_id>', methods=['GET'])
@login_required('customer')
def get_restaurant_detail(restaurant_id):
    restaurant = query_db('''
        SELECT restaurant_id, name, tagline, description, cuisine_type, rating, total_ratings,
               prep_time_min, is_accepting_orders, address, phone
        FROM restaurants
        WHERE restaurant_id = %s
    ''', (restaurant_id,), one=True)

    if not restaurant:
        return jsonify({'success': False, 'error': 'Restaurant not found.'}), 404

    restaurant['rating'] = float(restaurant['rating'])

    items = query_db('''
        SELECT m.item_id, m.category_id, c.name AS category_name, m.name, m.description,
               m.price, m.is_veg, m.is_available, m.stock_quantity, m.image_letter,
               m.badge_bg, m.badge_text
        FROM menu_items m
        JOIN categories c ON m.category_id = c.category_id
        WHERE m.restaurant_id = %s
        ORDER BY c.display_order ASC, m.price ASC
    ''', (restaurant_id,))

    for item in items:
        item['price'] = float(item['price'])

    return jsonify({
        'success': True,
        'restaurant': restaurant,
        'menu_items': items
    })


@customer_bp.route('/api/customer/dishes', methods=['GET'])
@login_required('customer')
def search_dishes():
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    category_name = request.args.get('category', '').strip()
    veg_only = request.args.get('veg', type=int)

    sql = '''
        SELECT m.item_id, m.restaurant_id, r.name AS restaurant_name, r.rating AS restaurant_rating,
               r.prep_time_min, m.category_id, c.name AS category_name, m.name, m.description,
               m.price, m.is_veg, m.is_available, m.stock_quantity, m.image_letter,
               m.badge_bg, m.badge_text
        FROM menu_items m
        JOIN restaurants r ON m.restaurant_id = r.restaurant_id
        JOIN categories c ON m.category_id = c.category_id
        WHERE 1=1
    '''
    params = []

    if q:
        sql += ' AND (m.name LIKE %s OR m.description LIKE %s OR r.name LIKE %s)'
        like_q = f'%{q}%'
        params.extend([like_q, like_q, like_q])

    if category_id:
        sql += ' AND m.category_id = %s'
        params.append(category_id)
    elif category_name:
        sql += ' AND c.name LIKE %s'
        params.append(f'%{category_name}%')

    if veg_only:
        sql += ' AND m.is_veg = 1'

    sql += ' ORDER BY m.is_available DESC, r.rating DESC, m.price ASC LIMIT 60'

    dishes = query_db(sql, tuple(params))
    for d in dishes:
        d['price'] = float(d['price'])
        d['restaurant_rating'] = float(d['restaurant_rating'])

    return jsonify({'success': True, 'dishes': dishes})


@customer_bp.route('/api/customer/addresses', methods=['GET', 'POST'])
@login_required('customer')
def manage_addresses():
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    if request.method == 'GET':
        addresses = query_db('''
            SELECT address_id, label, address_line, landmark, city, postal_code, is_default
            FROM addresses
            WHERE customer_id = %s
            ORDER BY is_default DESC, address_id DESC
        ''', (customer_id,))
        return jsonify({'success': True, 'addresses': addresses})

    # POST: Add new address
    data = request.get_json() or {}
    label = data.get('label', 'Home').strip()
    address_line = data.get('address_line', '').strip()
    landmark = data.get('landmark', '').strip()
    city = data.get('city', 'Bengaluru').strip()
    postal_code = data.get('postal_code', '560034').strip()
    is_default = 1 if data.get('is_default') else 0

    if not address_line or not postal_code:
        return jsonify({'success': False, 'error': 'Address line and postal code are required.'}), 400

    if is_default:
        query_db('UPDATE addresses SET is_default = 0 WHERE customer_id = %s', (customer_id,), commit=True)

    res = query_db('''
        INSERT INTO addresses (customer_id, label, address_line, landmark, city, postal_code, is_default)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (customer_id, label, address_line, landmark, city, postal_code, is_default), commit=True)

    return jsonify({
        'success': True,
        'message': 'Address added successfully!',
        'address_id': res['lastrowid']
    }), 201


@customer_bp.route('/api/customer/addresses/<int:address_id>/default', methods=['PUT', 'POST'])
@login_required('customer')
def set_default_address(address_id):
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    query_db('UPDATE addresses SET is_default = 0 WHERE customer_id = %s', (customer_id,), commit=True)
    query_db('UPDATE addresses SET is_default = 1 WHERE customer_id = %s AND address_id = %s', (customer_id, address_id), commit=True)
    return jsonify({'success': True, 'message': 'Default address updated.'})


@customer_bp.route('/api/customer/coupon/validate', methods=['POST'])
@login_required('customer')
def validate_coupon():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    subtotal = float(data.get('subtotal', 0.0))

    if not code:
        return jsonify({'success': False, 'error': 'Coupon code is required.'}), 400

    coupon = query_db('''
        SELECT coupon_id, code, discount_percentage, flat_discount, max_discount, min_order_amount, is_active, valid_until
        FROM coupons
        WHERE code = %s AND is_active = 1 AND valid_until >= NOW()
    ''', (code,), one=True)

    if not coupon:
        return jsonify({'success': False, 'error': 'Invalid or expired coupon code.'}), 404

    min_order = float(coupon['min_order_amount'])
    if subtotal < min_order:
        return jsonify({
            'success': False,
            'error': f'Minimum order amount of ₹{min_order:.0f} required for coupon {code}.'
        }), 400

    max_disc = float(coupon['max_discount'])
    disc_pct = float(coupon['discount_percentage'])
    flat_disc = float(coupon['flat_discount'])

    discount = 0.0
    if disc_pct > 0:
        discount = min(max_disc, round(subtotal * (disc_pct / 100.0), 2))
    elif flat_disc > 0:
        discount = min(max_disc, flat_disc)

    return jsonify({
        'success': True,
        'coupon_id': coupon['coupon_id'],
        'code': coupon['code'],
        'discount': discount,
        'message': f'Coupon {code} applied! ₹{discount:.2f} discount.'
    })


@customer_bp.route('/api/customer/order', methods=['POST'])
@login_required('customer')
def place_order_endpoint():
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    data = request.get_json() or {}

    restaurant_id = data.get('restaurant_id')
    address_id = data.get('address_id')
    coupon_code = (data.get('coupon_code') or '').strip()
    payment_method = (data.get('payment_method') or 'online').strip().lower()
    special_instructions = (data.get('special_instructions') or '').strip()
    items = data.get('items', [])

    if not restaurant_id or not items:
        return jsonify({'success': False, 'error': 'Restaurant and cart items are required.'}), 400

    if not address_id:
        def_addr = query_db('SELECT address_id FROM addresses WHERE customer_id = %s AND is_default = 1', (customer_id,), one=True)
        if not def_addr:
            def_addr = query_db('SELECT address_id FROM addresses WHERE customer_id = %s LIMIT 1', (customer_id,), one=True)
        if not def_addr:
            return jsonify({'success': False, 'error': 'Please provide or save a delivery address first.'}), 400
        address_id = def_addr['address_id']

    # Call Stored Procedure place_order
    items_json = json.dumps(items)
    args = [
        int(customer_id),
        int(restaurant_id),
        int(address_id),
        coupon_code if coupon_code else None,
        payment_method,
        special_instructions if special_instructions else None,
        items_json,
        0,  # OUT p_order_id
        ''  # OUT p_status_message
    ]

    try:
        proc_result = call_procedure('place_order', args)
        order_id = proc_result.get('place_order_arg8')
        status_message = proc_result.get('place_order_arg9')

        if not order_id:
            return jsonify({'success': False, 'error': status_message or 'Failed to place order.'}), 400

        # Fetch newly created order details
        order = query_db('''
            SELECT o.order_id, o.order_status, o.subtotal, o.discount_amount, o.delivery_fee,
                   o.tax_amount, o.total_amount, o.estimated_delivery_minutes, o.placed_at,
                   r.name AS restaurant_name
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.restaurant_id
            WHERE o.order_id = %s
        ''', (order_id,), one=True)

        for k in ['subtotal', 'discount_amount', 'delivery_fee', 'tax_amount', 'total_amount']:
            order[k] = float(order[k])
        order['placed_at'] = order['placed_at'].isoformat()

        return jsonify({
            'success': True,
            'message': status_message,
            'order': order
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@customer_bp.route('/api/customer/orders', methods=['GET'])
@login_required('customer')
def get_order_history():
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    orders = query_db('''
        SELECT o.order_id, o.restaurant_id, r.name AS restaurant_name, r.cuisine_type,
               o.order_status, o.total_amount, o.placed_at, o.delivered_at,
               p.payment_method, p.payment_status,
               rev.restaurant_rating, rev.review_text
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        JOIN payments p ON o.order_id = p.order_id
        LEFT JOIN reviews rev ON o.order_id = rev.order_id
        WHERE o.customer_id = %s
        ORDER BY o.placed_at DESC
    ''', (customer_id,))

    for o in orders:
        o['total_amount'] = float(o['total_amount'])
        o['placed_at'] = o['placed_at'].isoformat() if o['placed_at'] else None
        o['delivered_at'] = o['delivered_at'].isoformat() if o['delivered_at'] else None

        # Fetch items for this order
        items = query_db('''
            SELECT item_name, quantity, unit_price, item_total
            FROM order_items
            WHERE order_id = %s
        ''', (o['order_id'],))
        for it in items:
            it['unit_price'] = float(it['unit_price'])
            it['item_total'] = float(it['item_total'])
        o['items'] = items

    return jsonify({'success': True, 'orders': orders})


@customer_bp.route('/api/customer/order/<int:order_id>/status', methods=['GET'])
@login_required('customer')
def get_order_live_status(order_id):
    """Live order tracking endpoint polled every 4-5 seconds by the UI."""
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    order = query_db('''
        SELECT o.order_id, o.customer_id, o.restaurant_id, r.name AS restaurant_name,
               r.address AS restaurant_address, r.phone AS restaurant_phone, r.prep_time_min,
               o.order_status, o.subtotal, o.discount_amount, o.delivery_fee,
               o.tax_amount, o.total_amount, o.estimated_delivery_minutes,
               o.placed_at, o.accepted_at, o.ready_at, o.picked_at, o.delivered_at, o.cancelled_at,
               o.delivery_partner_id, u_dp.full_name AS partner_name, u_dp.phone AS partner_phone,
               dp.vehicle_type, dp.vehicle_number, dp.rating AS partner_rating,
               del.distance_km, del.status AS delivery_status,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.accepted_at, o.placed_at), NOW()) AS elapsed_prep_min,
               TIMESTAMPDIFF(MINUTE, COALESCE(o.picked_at, NOW()), NOW()) AS elapsed_transit_min
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.restaurant_id
        LEFT JOIN delivery_partners dp ON o.delivery_partner_id = dp.partner_id
        LEFT JOIN users u_dp ON dp.user_id = u_dp.user_id
        LEFT JOIN deliveries del ON o.order_id = del.order_id
        WHERE o.order_id = %s AND o.customer_id = %s
    ''', (order_id, customer_id), one=True)

    if not order:
        return jsonify({'success': False, 'error': 'Order not found.'}), 404

    for k in ['subtotal', 'discount_amount', 'delivery_fee', 'tax_amount', 'total_amount']:
        order[k] = float(order[k])
    if order.get('distance_km'):
        order['distance_km'] = float(order['distance_km'])

    # Format dates
    for k in ['placed_at', 'accepted_at', 'ready_at', 'picked_at', 'delivered_at', 'cancelled_at']:
        if order.get(k):
            order[k] = order[k].isoformat()

    # Dynamic delivery time estimation
    order_st = order['order_status']
    prep_min = order.get('prep_time_min') or 20
    elapsed_p = order.get('elapsed_prep_min') or 0
    rem_prep = max(2, prep_min - elapsed_p)

    if order_st in ('Placed', 'Accepted'):
        order['estimated_delivery_minutes'] = prep_min + 12
        order['eta_status_text'] = 'Order Confirmed · Preparing soon'
        order['step_index'] = 0
    elif order_st == 'Preparing':
        order['estimated_delivery_minutes'] = rem_prep + 12
        order['eta_status_text'] = f'Kitchen is cooking · ~{rem_prep}m left'
        order['step_index'] = 1
    elif order_st == 'Ready':
        order['estimated_delivery_minutes'] = 12
        order['eta_status_text'] = 'Food is ready · Rider picking up'
        order['step_index'] = 1
    elif order_st == 'Picked up':
        elapsed_tr = order.get('elapsed_transit_min') or 0
        rem_tr = max(2, 12 - elapsed_tr)
        order['estimated_delivery_minutes'] = rem_tr
        order['eta_status_text'] = f'Out for delivery · ~{rem_tr}m away'
        order['step_index'] = 2
    elif order_st == 'Delivered':
        order['estimated_delivery_minutes'] = 0
        order['eta_status_text'] = 'Delivered! Enjoy your food'
        order['step_index'] = 3
    else:
        order['estimated_delivery_minutes'] = 0
        order['eta_status_text'] = order_st
        order['step_index'] = -1

    order['has_rider'] = bool(order.get('delivery_partner_id') and order.get('partner_name'))

    # Fetch items
    items = query_db('''
        SELECT item_name, quantity, unit_price, item_total
        FROM order_items
        WHERE order_id = %s
    ''', (order_id,))
    for it in items:
        it['unit_price'] = float(it['unit_price'])
        it['item_total'] = float(it['item_total'])
    order['items'] = items

    return jsonify({'success': True, 'order': order})


@customer_bp.route('/api/customer/order/<int:order_id>/cancel', methods=['POST'])
@login_required('customer')
def cancel_order_endpoint(order_id):
    user_id = getattr(request, 'user_id', None) or session.get('user_id')
    data = request.get_json() or {}
    reason = data.get('reason', 'Customer requested cancellation')

    args = [order_id, user_id, reason, 0, '']
    try:
        proc_result = call_procedure('cancel_order', args)
        success = proc_result.get('cancel_order_arg4')
        message = proc_result.get('cancel_order_arg5')

        if not success:
            return jsonify({'success': False, 'error': message}), 400

        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@customer_bp.route('/api/customer/order/<int:order_id>/review', methods=['POST'])
@login_required('customer')
def submit_review(order_id):
    customer_id = getattr(request, 'entity_id', None) or session.get('entity_id')
    data = request.get_json() or {}

    rest_rating = int(data.get('restaurant_rating', 5))
    partner_rating = data.get('partner_rating')
    review_text = (data.get('review_text') or '').strip()

    order = query_db('SELECT restaurant_id, delivery_partner_id, order_status FROM orders WHERE order_id = %s AND customer_id = %s', (order_id, customer_id), one=True)
    if not order:
        return jsonify({'success': False, 'error': 'Order not found.'}), 404

    if order['order_status'] != 'Delivered':
        return jsonify({'success': False, 'error': 'Reviews can only be submitted for delivered orders.'}), 400

    existing = query_db('SELECT review_id FROM reviews WHERE order_id = %s', (order_id,), one=True)
    if existing:
        return jsonify({'success': False, 'error': 'Review has already been submitted for this order.'}), 400

    query_db('''
        INSERT INTO reviews (order_id, customer_id, restaurant_id, partner_id, restaurant_rating, partner_rating, review_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (order_id, customer_id, order['restaurant_id'], order['delivery_partner_id'], rest_rating, partner_rating, review_text), commit=True)

    # Recalculate restaurant rating
    query_db('''
        UPDATE restaurants r
        SET rating = (SELECT ROUND(AVG(restaurant_rating), 1) FROM reviews WHERE restaurant_id = r.restaurant_id),
            total_ratings = (SELECT COUNT(*) FROM reviews WHERE restaurant_id = r.restaurant_id)
        WHERE restaurant_id = %s
    ''', (order['restaurant_id'],), commit=True)

    return jsonify({'success': True, 'message': 'Thank you! Your review has been saved.'}), 201

