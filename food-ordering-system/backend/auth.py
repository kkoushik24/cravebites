"""
Authentication routes and role-based access control decorators.
Supports both RFC 7519 JWT in the Authorization header (Bearer <token>)
and Flask session cookies.
"""

import os
import time
import json
import hmac
import hashlib
import base64
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_db

auth_bp = Blueprint('auth', __name__)
JWT_SECRET = os.getenv('SECRET_KEY', 'dabba_super_secret_session_key_2026_sem3_dbms')

# -----------------------------------------------------------------------------
# Zero-dependency RFC 7519 compliant JWT implementation
# -----------------------------------------------------------------------------
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_jwt_token(payload: dict, expires_in: int = 86400 * 7) -> str:
    """Generate an HS256 signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    body = payload.copy()
    body['iat'] = int(time.time())
    body['exp'] = int(time.time()) + expires_in

    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    body_b64 = _b64url_encode(json.dumps(body, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{header_b64}.{body_b64}".encode('utf-8')
    sig = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{body_b64}.{sig_b64}"

def verify_jwt_token(token: str) -> dict:
    """Verify and decode an HS256 signed JWT token. Raises ValueError on failure."""
    if not token:
        raise ValueError("Token is required")
    parts = token.strip().split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    header_b64, body_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{body_b64}".encode('utf-8')
    expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid signature")
    payload = json.loads(_b64url_decode(body_b64).decode('utf-8'))
    if payload.get('exp') and time.time() > payload['exp']:
        raise ValueError("Token has expired")
    return payload


# -----------------------------------------------------------------------------
# Decorator: login_required
# -----------------------------------------------------------------------------
def login_required(roles=None):
    """
    Decorator to restrict access to authenticated users and specific roles.
    Checks Authorization: Bearer <token> first, falls back to session.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = None
            user_role = None
            entity_id = None

            # 1. Try JWT from Authorization Header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:].strip()
                try:
                    payload = verify_jwt_token(token)
                    user_id = payload.get('user_id')
                    user_role = payload.get('role')
                    entity_id = payload.get('entity_id')
                    request.current_user = payload
                    request.entity_id = entity_id
                    request.user_id = user_id
                    request.user_role = user_role
                except Exception:
                    return jsonify({'success': False, 'error': 'Invalid or expired authorization token.'}), 401

            # 2. Fall back to Flask session
            if not user_id:
                user_id = session.get('user_id')
                user_role = session.get('role')
                entity_id = session.get('entity_id')
                request.entity_id = entity_id
                request.user_id = user_id
                request.user_role = user_role

            if not user_id:
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'success': False, 'error': 'Authentication required. Please log in.'}), 401
                return redirect(url_for('auth.login_page', next=request.path))

            if roles and user_role not in roles:
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'success': False, 'error': f'Access denied: requires role {roles}.'}), 403
                flash('Access denied: You do not have permission to view that page.', 'error')
                if user_role == 'customer':
                    return redirect('/customer')
                elif user_role == 'restaurant':
                    return redirect('/restaurant')
                elif user_role == 'delivery_partner':
                    return redirect('/delivery')
                return redirect(url_for('auth.login_page'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET'])
def login_page():
    if session.get('user_id'):
        role = session.get('role')
        if role == 'customer':
            return redirect('/customer')
        elif role == 'restaurant':
            return redirect('/restaurant')
        elif role == 'delivery_partner':
            return redirect('/delivery')
    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    if session.get('user_id'):
        return redirect('/')
    return render_template('auth/signup.html')


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required.'}), 400

    # Retrieve user and role via parameterized query
    user = query_db('''
        SELECT u.user_id, u.role_id, r.role_name, u.full_name, u.email, u.phone, u.password_hash, u.is_active
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.email = %s
    ''', (email,), one=True)

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid email or password.'}), 401

    if not user['is_active']:
        return jsonify({'success': False, 'error': 'This account has been deactivated.'}), 403

    # Resolve entity ID (customer_id, restaurant_id, or partner_id)
    entity_id = None
    role = user['role_name']
    if role == 'customer':
        c = query_db('SELECT customer_id FROM customers WHERE user_id = %s', (user['user_id'],), one=True)
        entity_id = c['customer_id'] if c else None
    elif role == 'restaurant':
        r = query_db('SELECT restaurant_id FROM restaurants WHERE user_id = %s', (user['user_id'],), one=True)
        entity_id = r['restaurant_id'] if r else None
    elif role == 'delivery_partner':
        dp = query_db('SELECT partner_id FROM delivery_partners WHERE user_id = %s', (user['user_id'],), one=True)
        entity_id = dp['partner_id'] if dp else None

    # Generate JWT Token
    jwt_payload = {
        'user_id': user['user_id'],
        'role': role,
        'full_name': user['full_name'],
        'email': user['email'],
        'entity_id': entity_id
    }
    token = create_jwt_token(jwt_payload)

    # Also set session for backward compatibility
    session['user_id'] = user['user_id']
    session['role'] = role
    session['full_name'] = user['full_name']
    session['email'] = user['email']
    session['entity_id'] = entity_id

    redirect_map = {
        'customer': '/customer',
        'restaurant': '/restaurant',
        'delivery_partner': '/delivery'
    }
    redirect_url = redirect_map.get(role, '/')

    return jsonify({
        'success': True,
        'message': f'Welcome back, {user["full_name"]}!',
        'token': token,
        'redirect_url': redirect_url,
        'user': {
            'user_id': user['user_id'],
            'role': role,
            'full_name': user['full_name'],
            'email': user['email'],
            'entity_id': entity_id
        }
    })


@auth_bp.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or request.form
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    role_name = data.get('role', 'customer').strip().lower()

    if not full_name or not email or not phone or not password:
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters long.'}), 400

    if role_name not in ['customer', 'restaurant', 'delivery_partner']:
        role_name = 'customer'

    existing = query_db('SELECT user_id, email, phone FROM users WHERE email = %s OR phone = %s', (email, phone), one=True)
    if existing:
        if existing['email'] == email:
            return jsonify({'success': False, 'error': 'An account with this email already exists.'}), 409
        return jsonify({'success': False, 'error': 'An account with this phone number already exists.'}), 409

    role_record = query_db('SELECT role_id FROM roles WHERE role_name = %s', (role_name,), one=True)
    if not role_record:
        return jsonify({'success': False, 'error': 'Invalid role specified.'}), 400

    pwd_hash = generate_password_hash(password)

    res = query_db('''
        INSERT INTO users (role_id, full_name, email, phone, password_hash)
        VALUES (%s, %s, %s, %s, %s)
    ''', (role_record['role_id'], full_name, email, phone, pwd_hash), commit=True)
    new_user_id = res['lastrowid']

    entity_id = None
    if role_name == 'customer':
        c_res = query_db('INSERT INTO customers (user_id) VALUES (%s)', (new_user_id,), commit=True)
        entity_id = c_res['lastrowid']
        query_db('''
            INSERT INTO addresses (customer_id, label, address_line, city, postal_code, is_default)
            VALUES (%s, 'Home', '1st Main Road, Koramangala', 'Bengaluru', '560034', 1)
        ''', (entity_id,), commit=True)
    elif role_name == 'restaurant':
        r_res = query_db('''
            INSERT INTO restaurants (user_id, name, cuisine_type, address, phone)
            VALUES (%s, %s, 'North Indian, Street Food', 'Bengaluru Market', %s)
        ''', (new_user_id, full_name, phone), commit=True)
        entity_id = r_res['lastrowid']
    elif role_name == 'delivery_partner':
        dp_res = query_db('''
            INSERT INTO delivery_partners (user_id, vehicle_type, vehicle_number)
            VALUES (%s, 'Bike', 'KA-01-XX-0000')
        ''', (new_user_id,), commit=True)
        entity_id = dp_res['lastrowid']

    jwt_payload = {
        'user_id': new_user_id,
        'role': role_name,
        'full_name': full_name,
        'email': email,
        'entity_id': entity_id
    }
    token = create_jwt_token(jwt_payload)

    session['user_id'] = new_user_id
    session['role'] = role_name
    session['full_name'] = full_name
    session['email'] = email
    session['entity_id'] = entity_id

    redirect_map = {
        'customer': '/customer',
        'restaurant': '/restaurant',
        'delivery_partner': '/delivery'
    }

    return jsonify({
        'success': True,
        'message': 'Account created successfully!',
        'token': token,
        'redirect_url': redirect_map.get(role_name, '/')
    }), 201


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/api/auth/current_user', methods=['GET'])
def current_user():
    user_id = getattr(request, 'user_id', None) or session.get('user_id')
    user_role = getattr(request, 'user_role', None) or session.get('role')
    full_name = session.get('full_name')
    email = session.get('email')
    entity_id = getattr(request, 'entity_id', None) or session.get('entity_id')

    if not user_id:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                payload = verify_jwt_token(auth_header[7:].strip())
                user_id = payload.get('user_id')
                user_role = payload.get('role')
                full_name = payload.get('full_name')
                email = payload.get('email')
                entity_id = payload.get('entity_id')
            except Exception:
                pass

    if not user_id:
        return jsonify({'logged_in': False, 'success': False})

    user_dict = {
        'user_id': user_id,
        'role': user_role,
        'full_name': full_name,
        'email': email,
        'entity_id': entity_id
    }

    return jsonify({
        'success': True,
        'logged_in': True,
        'user': user_dict,
        **user_dict
    })
