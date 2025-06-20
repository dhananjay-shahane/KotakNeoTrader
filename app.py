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
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure Flask for Replit deployment
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SERVER_NAME'] = None  # Allow any host for Replit compatibility

# Additional configurations for proper external access
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
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
try:
    from supabase_client import SupabaseClient
    supabase_client = SupabaseClient()
except Exception as e:
    print(f"Supabase client initialization failed: {e}")
    supabase_client = None

neo_client = NeoClient()
trading_functions = TradingFunctions()
user_manager = UserManager()
session_helper = SessionHelper()
websocket_handler = WebSocketHandler()

# Log Supabase connection status
try:
    if supabase_client and supabase_client.is_connected():
        logging.info("✅ Supabase integration active")
    else:
        logging.warning("⚠️ Supabase not configured, using local database only")
except:
    logging.warning("⚠️ Supabase not configured, using local database only")

def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Real-time mode - use actual Kotak Neo API authentication
        demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
        if demo_mode:
            if not session.get('authenticated'):
                session['authenticated'] = True
                session['ucc'] = 'DEMO001'
                session['greeting_name'] = 'Demo User'
                session['access_token'] = 'demo_token'
                session['session_token'] = 'demo_session'
                session['client'] = 'demo_client'
                session.permanent = True
            return True
            
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
    """Home page - redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/test-csv')
def test_csv():
    """Test CSV data integration without authentication"""
    try:
        from trading_functions import TradingFunctions
        trading_func = TradingFunctions()
        
        # Get dashboard data from CSV
        dashboard_data = trading_func.get_dashboard_data(None)
        
        # Format for display
        positions = dashboard_data.get('positions', [])
        summary = dashboard_data.get('summary', {})
        
        html = f"""
        <html>
        <head><title>CSV Data Test</title></head>
        <body>
            <h1>ETF Trading Data from CSV</h1>
            <h2>Portfolio Summary</h2>
            <p>Total Positions: {summary.get('total_positions', 0)}</p>
            <p>Total Investment: ₹{summary.get('total_investment', 0):,.2f}</p>
            <p>Total P&L: ₹{summary.get('total_pnl', 0):,.2f}</p>
            
            <h2>Current Positions</h2>
            <table border="1">
                <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Entry Price</th>
                    <th>Current Price</th>
                    <th>Investment</th>
                    <th>P&L</th>
                </tr>
        """
        
        for pos in positions:
            html += f"""
                <tr>
                    <td>{pos.get('symbol', '')}</td>
                    <td>{pos.get('quantity', 0)}</td>
                    <td>₹{pos.get('avg_price', 0):,.2f}</td>
                    <td>₹{pos.get('ltp', 0):,.2f}</td>
                    <td>₹{pos.get('value', 0):,.2f}</td>
                    <td>₹{pos.get('pnl', 0):,.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<html><body><h1>Error testing CSV data</h1><p>{str(e)}</p></body></html>"

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
def etf_signals():
    """ETF Trading Signals page"""
    return render_template('etf_signals.html')

@app.route('/etf-signals-advanced')
@require_auth
def etf_signals_advanced():
    """Advanced ETF Trading Signals page with datatable"""
    return render_template('etf_signals_datatable.html')

@app.route('/admin-signals-datatable')
@require_auth
def admin_signals_datatable():
    """Admin Trade Signals Datatable with Kotak Neo integration"""
    return render_template('admin_signals_datatable.html')

@app.route('/admin-signals')
@require_auth
def admin_signals():
    """Admin Panel for managing trading signals with advanced datatable"""
    return render_template('admin_signals_datatable.html')

@app.route('/admin-signals-basic')
@require_auth
def admin_signals_basic():
    """Basic Admin Panel for sending trading signals"""
    return render_template('admin_signals.html')

@app.route('/supabase-admin')
@require_auth
def supabase_admin():
    """Supabase Integration Admin Dashboard"""
    return render_template('supabase_admin.html')

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

@app.route('/api/etf-signals-data')
def get_etf_signals_data():
    """API endpoint to get ETF signals data from database (admin_trade_signals for user zhz3j)"""
    try:
        from models_etf import AdminTradeSignal, RealtimeQuote
        from models import User
        from datetime import datetime
        
        # Always show zhz3j user's signals for demo purposes
        zhz3j_user = User.query.filter(
            (User.ucc.ilike('%zhz3j%')) | 
            (User.greeting_name.ilike('%zhz3j%')) | 
            (User.user_id.ilike('%zhz3j%'))
        ).first()
        
        if zhz3j_user:
            signals = AdminTradeSignal.query.filter_by(target_user_id=zhz3j_user.id).all()
            logging.info(f"ETF Signals API: Found {len(signals)} signals for user zhz3j")
        else:
            signals = AdminTradeSignal.query.limit(15).all()
            logging.info(f"ETF Signals API: No zhz3j user found, showing {len(signals)} signals")
        
        signals_data = []
        for signal in signals:
            # Get latest quote for real-time current price
            latest_quote = RealtimeQuote.query.filter_by(
                symbol=signal.symbol
            ).order_by(RealtimeQuote.timestamp.desc()).first()
            
            # Calculate real-time values based on current database structure
            current_price = float(signal.current_price) if signal.current_price else float(signal.entry_price)
            if latest_quote:
                current_price = float(latest_quote.current_price)
                signal.current_price = latest_quote.current_price
                signal.last_update_time = datetime.utcnow()
                db.session.commit()
            
            entry_price = float(signal.entry_price)
            quantity = signal.quantity
            invested_amount = entry_price * quantity
            current_value = current_price * quantity
            profit_loss = current_value - invested_amount
            profit_loss_percent = ((current_price - entry_price) / entry_price) * 100
            target_price = float(signal.target_price) if signal.target_price else 0
            target_value_amount = target_price * quantity if target_price > 0 else 0
            target_profit_return = ((target_price - entry_price) / entry_price) * 100 if target_price > 0 else 0
            
            # Calculate days held
            entry_date = signal.created_at
            days_held = (datetime.utcnow() - entry_date).days if entry_date else 0
            
            # Simulate 30-day and 7-day performance
            thirty_day_perf = profit_loss_percent * 1.2  # Simulate historical performance
            seven_day_perf = profit_loss_percent * 0.8
            
            # Format data for frontend with all required fields
            signal_dict = {
                'id': signal.id,
                'etf': signal.symbol,  # ETF
                'thirty': f"{thirty_day_perf:.2f}%" if thirty_day_perf else '',  # 30
                'dh': str(days_held),  # DH
                'date': entry_date.strftime('%Y-%m-%d') if entry_date else '',  # Date
                'pos': 1 if signal.signal_type == 'BUY' else 0,  # Pos
                'qty': quantity,  # Qty
                'ep': round(entry_price, 2),  # EP
                'cmp': round(current_price, 2),  # CMP
                'change_pct': round(profit_loss_percent, 2),  # %Chan
                'inv': round(invested_amount, 2),  # Inv.
                'tp': round(target_price, 2) if target_price > 0 else 0,  # TP
                'tva': round(target_value_amount, 2),  # TVA
                'tpr': round(target_profit_return, 2),  # TPR
                'pl': round(profit_loss, 2),  # PL
                'ed': signal.expires_at.strftime('%Y-%m-%d') if signal.expires_at else '',  # ED
                'exp': signal.expires_at.strftime('%Y-%m-%d') if signal.expires_at else '',  # EXP
                'pr': f"{profit_loss_percent:.2f}%",  # PR
                'pp': '★★★' if signal.priority == 'HIGH' else '★★' if signal.priority == 'MEDIUM' else '★',  # PP
                'iv': round(invested_amount, 2),  # IV
                'ip': f"{profit_loss_percent:.2f}%",  # IP
                'nt': signal.signal_description or '',  # NT
                'qt': signal.last_update_time.strftime('%H:%M') if signal.last_update_time else '',  # Qt
                'seven': f"{seven_day_perf:.2f}%",  # 7
                'change2': round(profit_loss_percent, 2),  # %Ch
                'status': signal.status,
                'signal_type': signal.signal_type,
                'priority': signal.priority
            }
            signals_data.append(signal_dict)
        
        # Calculate portfolio summary
        total_investment = sum(float(s.get('inv', 0)) for s in signals_data)
        total_current_value = sum(float(s.get('inv', 0)) + float(s.get('pl', 0)) for s in signals_data)
        total_pnl = sum(float(s.get('pl', 0)) for s in signals_data)
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        portfolio_summary = {
            'total_positions': len(signals_data),
            'total_investment': total_investment,
            'current_value': total_current_value,
            'total_pnl': total_pnl,
            'return_percent': round(return_percent, 2),
            'active_positions': len([s for s in signals_data if s.get('status') == 'ACTIVE']),
            'closed_positions': len([s for s in signals_data if s.get('status') == 'CLOSED'])
        }
        
        logging.info(f"ETF Signals API: Returning {len(signals_data)} signals for user zhz3j")
        
        return jsonify({
            'success': True,
            'signals': signals_data,
            'total': len(signals_data),
            'portfolio': portfolio_summary
        })
        
    except Exception as e:
        logging.error(f"Error fetching ETF signals data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/populate-admin-signals')
def populate_admin_signals_endpoint():
    """API endpoint to populate admin_trade_signals table with sample ETF data"""
    try:
        from models_etf import AdminTradeSignal
        from models import User
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(ucc='admin').first()
        if not admin_user:
            admin_user = User(
                ucc='admin',
                mobile_number='9999999999',
                greeting_name='Admin User',
                user_id='admin',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
        
        # Create target user if not exists
        target_user = User.query.filter_by(ucc='zhz3j').first()
        if not target_user:
            target_user = User(
                ucc='zhz3j',
                mobile_number='9876543210',
                greeting_name='ETF Trader',
                user_id='zhz3j',
                is_active=True
            )
            db.session.add(target_user)
            db.session.commit()
        
        # Clear existing signals
        AdminTradeSignal.query.delete()
        db.session.commit()
        
        # Sample ETF signals data (admin sends this data to the table)
        etf_signals = [
            {
                'symbol': 'NIFTYBEES',
                'signal_type': 'BUY',
                'entry_price': Decimal('245.50'),
                'target_price': Decimal('260.00'),
                'stop_loss': Decimal('235.00'),
                'quantity': 100,
                'signal_title': 'NIFTY ETF - Bullish Breakout',
                'signal_description': 'Strong momentum with volume surge. Target 260.',
                'priority': 'HIGH'
            },
            {
                'symbol': 'BANKBEES',
                'signal_type': 'BUY',
                'entry_price': Decimal('520.75'),
                'target_price': Decimal('545.00'),
                'stop_loss': Decimal('505.00'),
                'quantity': 50,
                'signal_title': 'Bank ETF - Sector Rotation',
                'signal_description': 'Banking sector showing strength. Good risk-reward.',
                'priority': 'MEDIUM'
            },
            {
                'symbol': 'GOLDSHARE',
                'signal_type': 'SELL',
                'entry_price': Decimal('4850.00'),
                'target_price': Decimal('4720.00'),
                'stop_loss': Decimal('4920.00'),
                'quantity': 10,
                'signal_title': 'Gold ETF - Correction Expected',
                'signal_description': 'Overbought levels, expect pullback to 4720.',
                'priority': 'MEDIUM'
            },
            {
                'symbol': 'ITBEES',
                'signal_type': 'BUY',
                'entry_price': Decimal('425.30'),
                'target_price': Decimal('445.00'),
                'stop_loss': Decimal('415.00'),
                'quantity': 75,
                'signal_title': 'IT ETF - Tech Recovery',
                'signal_description': 'IT sector bouncing from support. Good entry.',
                'priority': 'HIGH'
            },
            {
                'symbol': 'LIQUIDBEES',
                'signal_type': 'BUY',
                'entry_price': Decimal('1000.00'),
                'target_price': Decimal('1002.00'),
                'stop_loss': Decimal('999.50'),
                'quantity': 200,
                'signal_title': 'Liquid ETF - Safe Haven',
                'signal_description': 'Market volatility hedge, low risk trade.',
                'priority': 'LOW'
            }
        ]
        
        # Create signals in admin_trade_signals table
        for signal_data in etf_signals:
            signal = AdminTradeSignal(
                admin_user_id=admin_user.id,
                target_user_id=target_user.id,
                symbol=signal_data['symbol'],
                trading_symbol=f"{signal_data['symbol']}-EQ",
                signal_type=signal_data['signal_type'],
                entry_price=signal_data['entry_price'],
                target_price=signal_data['target_price'],
                stop_loss=signal_data['stop_loss'],
                quantity=signal_data['quantity'],
                signal_title=signal_data['signal_title'],
                signal_description=signal_data['signal_description'],
                priority=signal_data['priority'],
                status='ACTIVE',
                created_at=datetime.now() - timedelta(days=1),
                signal_date=datetime.now().date(),
                expiry_date=(datetime.now() + timedelta(days=30)).date(),
                investment_amount=signal_data['entry_price'] * signal_data['quantity'],
                current_price=signal_data['entry_price'],
                current_value=signal_data['entry_price'] * signal_data['quantity'],
                pnl=Decimal('0.00'),
                pnl_percentage=Decimal('0.00')
            )
            db.session.add(signal)
        
        db.session.commit()
        
        total_signals = AdminTradeSignal.query.count()
        active_signals = AdminTradeSignal.query.filter_by(status='ACTIVE').count()
        
        logging.info(f"Successfully populated {len(etf_signals)} ETF signals in admin_trade_signals table")
        
        return jsonify({
            'success': True,
            'message': 'Successfully populated admin trade signals table',
            'total_signals': total_signals,
            'active_signals': active_signals,
            'created_signals': len(etf_signals),
            'admin_user_id': admin_user.id,
            'target_user_id': target_user.id,
            'note': 'ETF signals page will now fetch data from admin_trade_signals table and show real-time CMP from Kotak Neo quotes'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error populating admin signals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

from routes.auth import auth_bp
from routes.main import main_bp
from api.dashboard import dashboard_api
from api.trading import trading_api
# ETF signals blueprint will be registered separately

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(dashboard_api, url_prefix='/api')
app.register_blueprint(trading_api, url_prefix='/api')

# ETF Signals functionality will be handled by the blueprint

# Additional blueprints
try:
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.notifications import notifications_bp
    from api.realtime_quotes import quotes_bp
    from api.signals_datatable import datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp
    from api.admin_signals_api import admin_signals_bp
    from api.supabase_api import supabase_bp

    app.register_blueprint(etf_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(datatable_bp)
    app.register_blueprint(enhanced_etf_bp)
    app.register_blueprint(admin_signals_bp)
    app.register_blueprint(supabase_bp, url_prefix='/api')
    print("✓ Additional blueprints registered successfully")
    
    # Initialize realtime quotes scheduler
    try:
        from realtime_quotes_manager import start_quotes_scheduler
        start_quotes_scheduler()
        print("✓ Realtime quotes scheduler started")
    except Exception as e:
        print(f"Warning: Could not start quotes scheduler: {e}")
        
except ImportError as e:
    print(f"Warning: Could not import additional blueprint: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Start ETF data scheduler for real-time quotes
    try:
        from etf_data_scheduler import start_etf_data_scheduler
        start_etf_data_scheduler()
        logging.info("✅ ETF Data Scheduler initialized")
    except Exception as e:
        logging.error(f"❌ Failed to start ETF scheduler: {str(e)}")

    # Initialize admin signals scheduler for comprehensive Kotak Neo data updates (5-minute intervals)
    try:
        logging.info("Starting admin signals scheduler with Kotak Neo integration...")
        from admin_signals_scheduler import start_admin_signals_scheduler
        start_admin_signals_scheduler()
        logging.info("✅ Admin signals scheduler started - automatic updates every 5 minutes")
    except Exception as e:
        logging.error(f"❌ Failed to start admin signals scheduler: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)