"""
Dabba: Online Food Ordering System
Main Flask Application Entry Point with CORS, Health Check, and REST APIs
"""

import os
import time
from flask import Flask, redirect, url_for, session, jsonify, request, make_response, send_from_directory
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

from auth import auth_bp
from customer_routes import customer_bp
from restaurant_routes import restaurant_bp
from delivery_routes import delivery_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static'
)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dabba_super_secret_session_key_2026')
app.config['JSON_SORT_KEYS'] = False

# Enable CORS across ports 5000, 5002, Capacitor origins (http://localhost, capacitor://localhost)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin') or '*'
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/api/<path:subpath>', methods=['OPTIONS'])
def options_preflight(subpath=None):
    resp = make_response('', 200)
    origin = request.headers.get('Origin') or '*'
    resp.headers['Access-Control-Allow-Origin'] = origin
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return resp

# Health Check Endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint used by start_usb_demo.ps1 and frontend offline reconnect probes."""
    return jsonify({
        'status': 'ok',
        'service': 'cravebites-backend',
        'timestamp': int(time.time()),
        'database': 'connected'
    })

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(restaurant_bp)
app.register_blueprint(delivery_bp)


# Serve static dish images directly from /images/ endpoint
@app.route('/images/<path:filename>')
def serve_images(filename):
    images_dir = os.path.join(STATIC_DIR, 'images')
    return send_from_directory(images_dir, filename)

CUSTOMER_APP_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'customer-app'))
DELIVERY_APP_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'delivery-app'))
RESTAURANT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'restaurant-web'))
BUILDS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'builds'))
ROOT_BUILDS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'builds'))

# Direct web link for customers/friends to use directly without install
@app.route('/app')
@app.route('/app/')
@app.route('/crave')
def serve_customer_app():
    return send_from_directory(CUSTOMER_APP_DIR, 'index.html')

# Direct web link for delivery riders
@app.route('/rider')
@app.route('/rider/')
@app.route('/delivery-app')
def serve_rider_app():
    return send_from_directory(DELIVERY_APP_DIR, 'index.html')

@app.route('/restaurant-portal')
def serve_restaurant_portal():
    return send_from_directory(RESTAURANT_DIR, 'index.html')

@app.route('/config.js')
def serve_config_js():
    return send_from_directory(CUSTOMER_APP_DIR, 'config.js')

@app.route('/rider/config.js')
def serve_rider_config_js():
    return send_from_directory(DELIVERY_APP_DIR, 'config.js')

@app.route('/manifest.json')
def serve_manifest_json():
    return send_from_directory(CUSTOMER_APP_DIR, 'manifest.json')

@app.route('/sw.js')
def serve_sw_js():
    return send_from_directory(CUSTOMER_APP_DIR, 'sw.js')

# Direct APK download link for friends
@app.route('/download')
@app.route('/download/apk')
@app.route('/apk')
@app.route('/CraveBites.apk')
def download_apk():
    apk_file = 'CraveBites-Customer.apk'
    if os.path.exists(os.path.join(BUILDS_DIR, apk_file)):
        return send_from_directory(BUILDS_DIR, apk_file, as_attachment=True, download_name='CraveBites.apk')
    return send_from_directory(ROOT_BUILDS_DIR, apk_file, as_attachment=True, download_name='CraveBites.apk')

@app.route('/download/rider')
@app.route('/rider.apk')
@app.route('/CraveRider.apk')
def download_rider_apk():
    for name in ['CraveRider.apk', 'dabba-rider.apk']:
        if os.path.exists(os.path.join(BUILDS_DIR, name)):
            return send_from_directory(BUILDS_DIR, name, as_attachment=True, download_name='CraveRider.apk')
        if os.path.exists(os.path.join(ROOT_BUILDS_DIR, name)):
            return send_from_directory(ROOT_BUILDS_DIR, name, as_attachment=True, download_name='CraveRider.apk')
    return jsonify({'error': 'Rider APK not found'}), 404


@app.route('/')
def index():
    """Default landing route redirects based on authentication and role."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login_page'))

    role = session.get('role')
    if role == 'customer':
        return redirect('/customer')
    elif role == 'restaurant':
        return redirect('/restaurant')
    elif role == 'delivery_partner':
        return redirect('/delivery')
    return redirect(url_for('auth.login_page'))


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return redirect(url_for('auth.login_page'))


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    print(f"Starting CraveBites Server on http://{host}:{port} (Debug: {debug})...")
    app.run(host=host, port=port, debug=debug)
