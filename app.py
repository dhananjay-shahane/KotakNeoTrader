import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup library paths for pandas/numpy dependencies
def setup_library_paths():
    """Setup LD_LIBRARY_PATH for required libraries"""
    # Critical: Set library paths before any imports that might use them
    import os
    os.environ['LD_LIBRARY_PATH'] = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    print(f"Set LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")
    
    # Force reload of dynamic libraries by importing ctypes
    try:
        import ctypes
        import ctypes.util
        # Preload essential libraries
        libstdc = ctypes.util.find_library('stdc++')
        if libstdc:
            ctypes.CDLL(libstdc)
            print("Preloaded libstdc++")
    except Exception as e:
        print(f"Library preload warning: {e}")

# Setup environment before importing other modules
setup_library_paths()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "877ec8603e82bb360d188674c9909e08e69fba8333bce85cdec7d2298c34f02d")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    import models_etf  # noqa: F401

    db.create_all()

# Import and add routes
from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
import logging
import json
from datetime import datetime, timedelta

# Configure session for persistent storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
Session(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize helper classes
from neo_client import NeoClient
from trading_functions import TradingFunctions
from user_manager import UserManager
from session_helper import SessionHelper
from websocket_handler import WebSocketHandler

neo_client = NeoClient()
trading_functions = TradingFunctions()
user_manager = UserManager()
session_helper = SessionHelper()
websocket_handler = WebSocketHandler()

def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Check if user is authenticated
        if not session.get('authenticated'):
            return False

        # Check session expiration
        session_expires_at = session.get('session_expires_at')
        if session_expires_at:
            from datetime import datetime
            if datetime.now() > datetime.fromisoformat(session_expires_at):
                session.clear()
                return False

        # Check if required session data exists
        required_fields = ['access_token', 'session_token', 'ucc']
        for field in required_fields:
            if not session.get(field):
                logging.warning(f"Missing session field: {field}")
                session.clear()
                return False

        return True

    except Exception as e:
        logging.error(f"Session validation error: {e}")
        session.clear()
        return False

def require_auth(f):
    """Decorator to require authentication for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_current_session():
            return redirect(url_for('login', expired='true'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    if validate_current_session():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with TOTP authentication only"""
    # Check if session expired and show message
    session_expired = request.args.get('expired') == 'true'
    if session_expired:
        flash('Your session has expired. Please login again.', 'warning')
    if request.method == 'POST':
        try:
            # Get form data
            mobile_number = request.form.get('mobile_number', '').strip()
            ucc = request.form.get('ucc', '').strip()
            totp = request.form.get('totp', '').strip()
            mpin = request.form.get('mpin', '').strip()

            # Validate inputs
            if not all([mobile_number, ucc, totp, mpin]):
                flash('All fields are required', 'error')
                return render_template('login.html')

            # Validate formats
            if len(mobile_number) != 10 or not mobile_number.isdigit():
                flash('Mobile number must be 10 digits', 'error')
                return render_template('login.html')

            if len(totp) != 6 or not totp.isdigit():
                flash('TOTP must be 6 digits', 'error')
                return render_template('login.html')

            if len(mpin) != 6 or not mpin.isdigit():
                flash('MPIN must be 6 digits', 'error')
                return render_template('login.html')

            # Execute TOTP login
            result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)

            if result and result.get('success'):
                client = result.get('client')
                session_data = result.get('session_data', {})

                # Store in session
                session['authenticated'] = True
                session['access_token'] = session_data.get('access_token')
                session['session_token'] = session_data.get('session_token')
                session['sid'] = session_data.get('sid')
                session['ucc'] = ucc
                session['client'] = client
                session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                session['greeting_name'] = session_data.get('greetingName', ucc)
                session.permanent = True
                
                # Set session expiration (24 hours from now)
                expiry_time = datetime.now() + timedelta(hours=24)
                session['session_expires_at'] = expiry_time.isoformat()

                # Store additional user data
                session['rid'] = session_data.get('rid')
                session['user_id'] = session_data.get('user_id')
                session['client_code'] = session_data.get('client_code')
                session['is_trial_account'] = session_data.get('is_trial_account')

                # Store user data in database
                try:
                    login_response = {
                        'success': True,
                        'data': {
                            'ucc': ucc,
                            'mobile_number': mobile_number,
                            'greeting_name': session_data.get('greetingName'),
                            'user_id': session_data.get('user_id'),
                            'client_code': session_data.get('client_code'),
                            'product_code': session_data.get('product_code'),
                            'account_type': session_data.get('account_type'),
                            'branch_code': session_data.get('branch_code'),
                            'is_trial_account': session_data.get('is_trial_account', False),
                            'access_token': session_data.get('access_token'),
                            'session_token': session_data.get('session_token'),
                            'sid': session_data.get('sid'),
                            'rid': session_data.get('rid')
                        }
                    }

                    db_user = user_manager.create_or_update_user(login_response)
                    user_session = user_manager.create_user_session(db_user.id, login_response)

                    session['db_user_id'] = db_user.id
                    session['db_session_id'] = user_session.session_id

                    logging.info(f"User data stored in database for UCC: {ucc}")

                except Exception as db_error:
                    logging.error(f"Failed to store user data in database: {db_error}")

                flash('Successfully authenticated with TOTP!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error_msg = result.get('message', 'Authentication failed') if result else 'Login failed'
                flash(f'TOTP login failed: {error_msg}', 'error')

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with portfolio overview"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch dashboard data with error handling
        dashboard_data = {}
        try:
            raw_dashboard_data = trading_functions.get_dashboard_data(client)

            # Ensure dashboard_data is always a dictionary
            if isinstance(raw_dashboard_data, dict):
                dashboard_data = raw_dashboard_data
                # Validate that positions and holdings are lists
                if not isinstance(dashboard_data.get('positions'), list):
                    dashboard_data['positions'] = []
                if not isinstance(dashboard_data.get('holdings'), list):
                    dashboard_data['holdings'] = []
                if not isinstance(dashboard_data.get('limits'), dict):
                    dashboard_data['limits'] = {}
                if not isinstance(dashboard_data.get('recent_orders'), list):
                    dashboard_data['recent_orders'] = []
            elif isinstance(raw_dashboard_data, list):
                # If API returns a list directly, wrap it properly
                dashboard_data = {
                    'positions': raw_dashboard_data,
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': len(raw_dashboard_data),
                    'total_holdings': 0,
                    'total_orders': 0
                }
            else:
                # Fallback empty structure
                dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': 0,
                    'total_holdings': 0,
                    'total_orders': 0
                }

            # Ensure all required keys exist with default values
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])
            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            # For errors, show dashboard with empty data
            flash(f'Some data could not be loaded: {str(dashboard_error)}', 'warning')
            dashboard_data = {
                'positions': [],
                'holdings': [],
                'limits': {},
                'recent_orders': [],
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0
            }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        # Return dashboard with empty data structure
        empty_data = {
            'positions': [],
            'holdings': [],
            'limits': {},
            'recent_orders': [],
            'total_positions': 0,
            'total_holdings': 0,
            'total_orders': 0
        }
        return render_template('dashboard.html', data=empty_data)

@app.route('/positions')
@require_auth
def positions():
    """Positions page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch positions data
        positions_data = trading_functions.get_positions(client)
        
        # Ensure positions_data is a list
        if isinstance(positions_data, dict):
            if 'data' in positions_data:
                positions_list = positions_data['data']
            elif 'positions' in positions_data:
                positions_list = positions_data['positions']
            else:
                positions_list = []
        elif isinstance(positions_data, list):
            positions_list = positions_data
        else:
            positions_list = []
            
        return render_template('positions.html', positions=positions_list)
        
    except Exception as e:
        logging.error(f"Positions page error: {e}")
        flash(f'Error loading positions: {str(e)}', 'error')
        return render_template('positions.html', positions=[])

@app.route('/holdings')
@require_auth
def holdings():
    """Holdings page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch holdings data
        holdings_data = trading_functions.get_holdings(client)
        
        # Ensure holdings_data is a list
        if isinstance(holdings_data, dict):
            if 'data' in holdings_data:
                holdings_list = holdings_data['data']
            elif 'holdings' in holdings_data:
                holdings_list = holdings_data['holdings']
            else:
                holdings_list = []
        elif isinstance(holdings_data, list):
            holdings_list = holdings_data
        else:
            holdings_list = []
            
        return render_template('holdings.html', holdings=holdings_list)
        
    except Exception as e:
        logging.error(f"Holdings page error: {e}")
        flash(f'Error loading holdings: {str(e)}', 'error')
        return render_template('holdings.html', holdings=[])

@app.route('/orders')
@require_auth
def orders():
    """Orders page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch orders data
        orders_data = trading_functions.get_orders(client)
        
        # Ensure orders_data is a list
        if isinstance(orders_data, dict):
            if 'data' in orders_data:
                orders_list = orders_data['data']
            elif 'orders' in orders_data:
                orders_list = orders_data['orders']
            else:
                orders_list = []
        elif isinstance(orders_data, list):
            orders_list = orders_data
        else:
            orders_list = []
            
        return render_template('orders.html', orders=orders_list)
        
    except Exception as e:
        logging.error(f"Orders page error: {e}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders.html', orders=[])

@app.route('/charts')
@require_auth
def charts():
    """Charts page for trading analysis"""

    return render_template('charts.html')

@app.route('/etf-signals')
@require_auth
def etf_signals():
    """ETF Trading Signals page"""
    return render_template('etf_signals.html')

# API endpoints
@app.route('/api/dashboard-data')
def get_dashboard_data_api():
    """AJAX endpoint for dashboard data without page refresh"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:


        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        dashboard_data = trading_functions.get_dashboard_data(client)
        return jsonify(dashboard_data)
    except Exception as e:
        logging.error(f"Dashboard data error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def get_positions_api():
    """API endpoint to get current positions"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        positions = trading_functions.get_positions(client)
        return jsonify(positions)
    except Exception as e:
        logging.error(f"Positions API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/holdings')
def get_holdings_api():
    """API endpoint to get holdings"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        holdings = trading_functions.get_holdings(client)
        return jsonify(holdings)
    except Exception as e:
        logging.error(f"Holdings API error: {e}")
        return jsonify({'error': str(e)}), 500

from routes.auth import auth_bp
from routes.main import main_bp
from api.dashboard import dashboard_api
from api.trading import trading_api
from api.etf_signals import (
    get_etf_positions, add_etf_position, update_etf_position, 
    delete_etf_position, search_etf_instruments, get_etf_quotes,
    get_portfolio_summary, bulk_update_positions
)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(dashboard_api, url_prefix='/api')
app.register_blueprint(trading_api, url_prefix='/api')

# ETF Signals API routes
@app.route('/api/etf/positions', methods=['GET'])
@require_auth
def api_get_etf_positions():
    return get_etf_positions()

@app.route('/api/etf/positions', methods=['POST'])
@require_auth
def api_add_etf_position():
    return add_etf_position()

@app.route('/api/etf/positions', methods=['PUT'])
@require_auth
def api_update_etf_position():
    return update_etf_position()

@app.route('/api/etf/positions', methods=['DELETE'])
@require_auth
def api_delete_etf_position():
    return delete_etf_position()

@app.route('/api/etf/search', methods=['GET'])
@require_auth
def api_search_etf_instruments():
    return search_etf_instruments()

@app.route('/api/etf/quotes', methods=['POST'])
@require_auth
def api_get_etf_quotes():
    return get_etf_quotes()

@app.route('/api/etf/portfolio-summary', methods=['GET'])
@require_auth
def api_get_portfolio_summary():
    return get_portfolio_summary()

@app.route('/api/etf/bulk-update', methods=['POST'])
@require_auth
def api_bulk_update_positions():
    return bulk_update_positions()

# Additional blueprints
try:
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.notifications import notifications_bp

    app.register_blueprint(etf_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    print("✓ Additional blueprints registered successfully")
except ImportError as e:
    print(f"Warning: Could not import additional blueprint: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)