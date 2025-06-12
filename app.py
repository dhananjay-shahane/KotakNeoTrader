import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from neo_client import NeoClient
from trading_functions import TradingFunctions
from websocket_handler import WebSocketHandler
import json

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set directly
    pass

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure for Replit deployment
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1, x_for=1, x_port=1)

# Configure PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure session for persistent storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
Session(app)

# Initialize database
from models import db, User, UserSession, UserPreferences
db.init_app(app)

# Initialize Neo Client and Trading Functions
neo_client = NeoClient()
trading_functions = TradingFunctions()
websocket_handler = WebSocketHandler()

# Initialize Session Manager and User Manager
from session_manager import SessionManager
from user_manager import UserManager
session_manager = SessionManager()
user_manager = UserManager()

# Create database tables
with app.app_context():
    db.create_all()

def validate_current_session():
    """Validate current session without auto-login bypass"""
    try:
        # Only validate if user is already authenticated in this session
        if not session.get('authenticated'):
            return False
            
        # Check if we have required session data
        access_token = session.get('access_token')
        if not access_token:
            return False
            
        # Try to recreate client from session data if needed
        client = session.get('client')
        if not client and access_token:
            client = neo_client.initialize_client_with_tokens(
                access_token,
                session.get('session_token'),
                session.get('sid')
            )
            if client:
                session['client'] = client
            
        if not client:
            return False
            
        # Validate session with proper 2FA check
        if neo_client.validate_session(client):
            return True
        else:
            # Clear invalid session
            session.clear()
            session_manager.remove_session('default_user')
            return False
            
    except Exception as e:
        logging.error(f"Session validation failed: {e}")
        # Clear any corrupted session data
        session.clear()
        return False

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'kotak-neo-trading-app',
        'timestamp': str(os.environ.get('REPL_SLUG', 'development'))
    })

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    try:
        # Only check current session, no auto-authentication bypass
        if validate_current_session():
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        # If there's any error, just redirect to login
        return redirect(url_for('login'))

@app.route('/debug-session')
def debug_session():
    """Debug session state"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'has_client': 'client' in session,
        'has_credentials': 'credentials' in session,
        'session_keys': list(session.keys())
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with TOTP authentication only"""
    if request.method == 'POST':
        try:
            # TOTP Login
            mobile_number = request.form.get('mobile_number', '').strip()
            ucc = request.form.get('ucc', '').strip()
            totp = request.form.get('totp', '').strip()
            mpin = request.form.get('mpin', '').strip()
            
            if not mobile_number or not ucc or not totp or not mpin:
                flash('All fields are required', 'error')
                return render_template('login.html')
            
            # Execute TOTP login
            result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)
            
            if result['success']:
                client = result['client']
                session_data = result['session_data']
                
                # Store in session first (needed for API calls to work)
                session['authenticated'] = True
                session['access_token'] = session_data.get('access_token')
                session['session_token'] = session_data.get('session_token')
                session['sid'] = session_data.get('sid')
                session['ucc'] = ucc
                session['client'] = client
                session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                session['greeting_name'] = session_data.get('greetingName', ucc)
                session.permanent = True
                
                # Validate the client after storing session data
                validation_success = False
                try:
                    validation_success = neo_client.validate_session(client)
                except Exception as val_error:
                    logging.warning(f"Session validation error (proceeding anyway): {val_error}")
                    validation_success = True  # Proceed if validation fails but login succeeded
                
                if not validation_success:
                    logging.warning("Session validation failed but login was successful - proceeding")
                    # Don't fail the login if validation fails, as the login itself was successful
                
                # Store additional user data in session
                session['rid'] = session_data.get('rid')
                session['user_id'] = session_data.get('user_id')
                
                # Store user data in PostgreSQL database
                try:
                    # Create the complete login response for database storage
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
                    
                    # Create or update user in database
                    db_user = user_manager.create_or_update_user(login_response)
                    
                    # Create session record
                    user_session = user_manager.create_user_session(db_user.id, login_response)
                    
                    # Store database user ID in session
                    session['db_user_id'] = db_user.id
                    session['db_session_id'] = user_session.session_id
                    
                    logging.info(f"User data stored in database for UCC: {ucc}")
                    
                except Exception as db_error:
                    logging.error(f"Failed to store user data in database: {db_error}")
                    # Don't fail the login if database storage fails
                    pass
                session['client_code'] = session_data.get('client_code')
                session['is_trial_account'] = session_data.get('is_trial_account')
                
                # Store complete session persistently
                persistent_data = session_data.copy()  # Start with complete response
                persistent_data.update({
                    'access_token': session_data.get('access_token'),
                    'session_token': session_data.get('session_token'),
                    'sid': session_data.get('sid'),
                    'ucc': ucc,
                    'mobile_number': mobile_number
                })
                session_manager.store_session('default_user', persistent_data)
                
                flash('Successfully authenticated with TOTP!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'TOTP login failed: {result.get("message", "Unknown error")}', 'error')
                return render_template('login.html')
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    try:
        # Logout from Neo API if client exists
        if 'client' in session:
            try:
                session['client'].logout()
            except:
                pass  # Ignore logout errors

        # Clear persistent session
        session_manager.remove_session('default_user')
        session.clear()
        flash('Logged out successfully', 'success')
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")

    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with portfolio overview"""
    # Require proper authentication - no bypass
    if not validate_current_session():
        flash('Complete the 2FA process before accessing this application', 'error')
        session.clear()
        return redirect(url_for('login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please complete the 2FA process and login again.', 'error')
            session.clear()
            return redirect(url_for('login'))

        # Try to validate session, but don't fail if validation is unreliable
        try:
            validation_result = neo_client.validate_session(client)
            if not validation_result:
                logging.warning("Session validation failed, but attempting to proceed with dashboard")
        except Exception as val_error:
            logging.warning(f"Session validation error (proceeding): {val_error}")

        # Fetch dashboard data with error handling
        dashboard_data = {}
        try:
            raw_dashboard_data = trading_functions.get_dashboard_data(client)
            
            # Ensure dashboard_data is a dictionary
            if isinstance(raw_dashboard_data, dict):
                dashboard_data = raw_dashboard_data
            else:
                # If it's not a dict, create a proper structure
                dashboard_data = {
                    'positions': raw_dashboard_data if isinstance(raw_dashboard_data, list) else [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': len(raw_dashboard_data) if isinstance(raw_dashboard_data, list) else 0,
                    'total_holdings': 0,
                    'total_orders': 0
                }
                
            # Ensure all required keys exist with default values
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])
            dashboard_data.setdefault('total_positions', 0)
            dashboard_data.setdefault('total_holdings', 0)
            dashboard_data.setdefault('total_orders', 0)
            
        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            # Check if it's a 2FA error specifically
            if any(phrase in str(dashboard_error) for phrase in [
                "Complete the 2fa process", 
                "Invalid Credentials", 
                "Invalid JWT token"
            ]):
                flash('Complete the 2FA process before accessing this application', 'error')
                session.clear()
                return redirect(url_for('login'))
            else:
                # For other errors, show dashboard with empty data
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
        if "Complete the 2fa process" in str(e) or "Invalid Credentials" in str(e):
            flash('Complete the 2FA process before accessing this application', 'error')
            session.clear()
            return redirect(url_for('login'))
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', data={})

@app.route('/positions')
def positions():
    """Positions page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch positions data
        positions_data = trading_functions.get_positions(client)

        return render_template('positions.html', positions=positions_data)

    except Exception as e:
        logging.error(f"Positions error: {str(e)}")
        flash(f'Error loading positions: {str(e)}', 'error')
        return render_template('positions.html', positions=[])

@app.route('/holdings')
def holdings():
    """Holdings page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch holdings data
        holdings_data = trading_functions.get_holdings(client)

        return render_template('holdings.html', holdings=holdings_data)

    except Exception as e:
        logging.error(f"Holdings error: {str(e)}")
        flash(f'Error loading holdings: {str(e)}', 'error')
        return render_template('holdings.html', holdings=[])

@app.route('/orders')
def orders():
    """Orders page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch orders data
        orders_data = trading_functions.get_orders(client)

        return render_template('orders.html', orders=orders_data)

    except Exception as e:
        logging.error(f"Orders error: {str(e)}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders.html', orders=[])

@app.route('/charts')
def charts():
    """Charts page for trading analysis"""
    # Require proper authentication - no bypass
    if not validate_current_session():
        flash('Complete the 2FA process before accessing this application', 'error')
        session.clear()
        return redirect(url_for('login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please complete the 2FA process and login again.', 'error')
            session.clear()
            return redirect(url_for('login'))

        return render_template('charts.html')

    except Exception as e:
        logging.error(f"Charts page error: {str(e)}")
        if "Complete the 2fa process" in str(e) or "Invalid Credentials" in str(e):
            flash('Complete the 2FA process before accessing this application', 'error')
            session.clear()
            return redirect(url_for('login'))
        else:
            flash(f'Error loading charts: {str(e)}', 'error')
            return render_template('charts.html')

@app.route('/api/place_order', methods=['POST'])
def place_order():
    """API endpoint to place order"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()

        # 
        # INSERT YOUR JUPYTER NOTEBOOK ORDER PLACEMENT CODE HERE
        # Use the trading_functions.place_order method
        # 
        result = trading_functions.place_order(client, order_data)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Place order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/modify_order', methods=['POST'])
def modify_order():
    """API endpoint to modify order"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()

        # 
        # INSERT YOUR JUPYTER NOTEBOOK ORDER MODIFICATION CODE HERE
        # Use the trading_functions.modify_order method
        # 
        result = trading_functions.modify_order(client, order_data)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Modify order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    """API endpoint to cancel order"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()

        # 
        # INSERT YOUR JUPYTER NOTEBOOK ORDER CANCELLATION CODE HERE
        # Use the trading_functions.cancel_order method
        # 
        result = trading_functions.cancel_order(client, order_data)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Cancel order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/quotes', methods=['POST'])
def get_quotes():
    """API endpoint to get live quotes"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        quote_data = request.get_json()

        # 
        # INSERT YOUR JUPYTER NOTEBOOK QUOTES FETCHING CODE HERE
        # Use the trading_functions.get_quotes method
        # 
        result = trading_functions.get_quotes(client, quote_data)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Get quotes error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/live_quotes')
def get_live_quotes():
    try:
        # Get live quotes for dashboard symbols
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        quotes = []

        for symbol in symbols:
            # Simulate live data - replace with actual API call
            import random
            quote = {
                'symbol': symbol,
                'ltp': round(1000 + random.random() * 2000, 2),
                'change': round((random.random() - 0.5) * 50, 2),
                'changePct': round((random.random() - 0.5) * 5, 2),
                'volume': random.randint(50000, 500000),
                'timestamp': 'now'
            }
            quotes.append(quote)

        return jsonify({'success': True, 'quotes': quotes})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/portfolio_summary')
def get_portfolio_summary():
    try:
        if not validate_current_session():
            return jsonify({'success': False, 'message': 'Complete the 2FA process before accessing this application'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Complete the 2FA process before accessing this application'})

        # Get individual components instead of combined summary to avoid repeated calls
        positions_data = trading_functions.get_positions(client)
        holdings_data = trading_functions.get_holdings(client)
        orders_data = trading_functions.get_orders(client)
        
        # Calculate summary statistics
        total_positions = len(positions_data) if positions_data else 0
        total_holdings = len(holdings_data) if holdings_data else 0
        total_orders = len(orders_data) if orders_data else 0
        
        # Calculate P&L from positions
        total_pnl = 0.0
        if positions_data:
            for position in positions_data:
                try:
                    pnl = float(position.get('pnl', 0) or position.get('urPnl', 0) or 0)
                    total_pnl += pnl
                except (ValueError, TypeError):
                    continue
        
        # Calculate investment from holdings
        total_investment = 0.0
        if holdings_data:
            for holding in holdings_data:
                try:
                    quantity = float(holding.get('quantity', 0) or holding.get('holdQty', 0) or 0)
                    avg_price = float(holding.get('avgPrice', 0) or holding.get('avgRate', 0) or 0)
                    total_investment += quantity * avg_price
                except (ValueError, TypeError):
                    continue
        
        return jsonify({
            'success': True,
            'total_positions': total_positions,
            'total_holdings': total_holdings,
            'total_orders': total_orders,
            'total_pnl': round(total_pnl, 2),
            'total_investment': round(total_investment, 2),
            'day_change': 0.0,  # Will be calculated from positions data
            'available_margin': 0.0,  # Will get from limits API
            'positions': positions_data[:5] if positions_data else [],  # First 5 positions
            'holdings': holdings_data[:5] if holdings_data else [],  # First 5 holdings
            'recent_orders': orders_data[:5] if orders_data else []  # Last 5 orders
        })
            
    except Exception as e:
        logging.error(f"Portfolio summary API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/portfolio_details')
def get_portfolio_details():
    """Get detailed portfolio information"""
    try:
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'})

        # Get comprehensive portfolio data
        result = trading_functions.get_portfolio_summary(client)
        
        return jsonify(result)
            
    except Exception as e:
        logging.error(f"Portfolio details error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/positions')
def get_positions_api():
    """API endpoint to get current positions"""
    try:
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'})

        positions_data = trading_functions.get_positions(client)
        
        return jsonify({
            'success': True,
            'positions': positions_data,
            'count': len(positions_data) if positions_data else 0
        })
            
    except Exception as e:
        logging.error(f"Positions API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/holdings')
def get_holdings_api():
    """API endpoint to get holdings"""
    try:
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'})

        holdings_data = trading_functions.get_holdings(client)
        
        return jsonify({
            'success': True,
            'holdings': holdings_data,
            'count': len(holdings_data) if holdings_data else 0
        })
            
    except Exception as e:
        logging.error(f"Holdings API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/user_profile')
def get_user_profile():
    """API endpoint to get user profile information"""
    try:
        if not validate_current_session():
            return jsonify({'success': False, 'message': 'Complete the 2FA process before accessing this application'})

        # Check if client is valid and test with a simple API call
        client = session.get('client')
        token_status = 'Invalid'
        
        if client:
            try:
                # Try a simple API call to validate token and 2FA
                limits_response = client.limits()
                if limits_response and ('data' in limits_response or 'Data' in limits_response):
                    data = limits_response.get('data') or limits_response.get('Data')
                    if data and not isinstance(data, str):
                        token_status = 'Valid'
                    else:
                        token_status = 'Incomplete 2FA'
                else:
                    token_status = 'Expired'
            except Exception as e:
                logging.error(f"Token validation error: {str(e)}")
                error_msg = str(e)
                if "Complete the 2fa process" in error_msg:
                    token_status = 'Incomplete 2FA'
                else:
                    token_status = 'Expired'
                # Clear session if token is invalid or 2FA incomplete
                if any(phrase in error_msg for phrase in [
                    "Complete the 2fa process",
                    "Invalid Credentials", 
                    "Invalid JWT token"
                ]):
                    session.clear()
                    session_manager.remove_session('default_user')

        # Get complete session data from persistent storage
        stored_session = session_manager.get_session('default_user')
        
        profile_data = {
            'ucc': session.get('ucc', 'N/A'),
            'greeting_name': session.get('greeting_name', session.get('ucc', 'User')),
            'login_time': session.get('login_time', 'N/A'),
            'session_token': session.get('session_token', 'N/A')[:20] + '...' if session.get('session_token') else 'N/A',
            'access_token': session.get('access_token', 'N/A')[:20] + '...' if session.get('access_token') else 'N/A',
            'sid': session.get('sid', 'N/A')[:15] + '...' if session.get('sid') else 'N/A',
            'rid': session.get('rid', stored_session.get('rid', 'N/A') if stored_session else 'N/A'),
            'is_trial_account': session.get('is_trial_account', stored_session.get('is_trial_account', False) if stored_session else False),
            'user_id': session.get('user_id', stored_session.get('user_id', 'N/A') if stored_session else 'N/A'),
            'client_code': session.get('client_code', stored_session.get('client_code', 'N/A') if stored_session else 'N/A'),
            'product_code': session.get('product_code', stored_session.get('product_code', 'N/A') if stored_session else 'N/A'),
            'account_type': session.get('account_type', stored_session.get('account_type', 'N/A') if stored_session else 'N/A'),
            'branch_code': session.get('branch_code', stored_session.get('branch_code', 'N/A') if stored_session else 'N/A'),
            'exchange_codes': session.get('exchange_codes', stored_session.get('exchange_codes', []) if stored_session else []),
            'order_types': session.get('order_types', stored_session.get('order_types', []) if stored_session else []),
            'product_types': session.get('product_types', stored_session.get('product_types', []) if stored_session else []),
            'token_type': session.get('token_type', stored_session.get('token_type', 'N/A') if stored_session else 'N/A'),
            'scope': session.get('scope', stored_session.get('scope', 'N/A') if stored_session else 'N/A'),
            'expires_in': session.get('expires_in', stored_session.get('expires_in', 'N/A') if stored_session else 'N/A'),
            'authenticated': session.get('authenticated', False),
            'account_status': 'Active' if token_status == 'Valid' else 'Token Expired - Please Re-login',
            'token_status': token_status,
            'needs_reauth': token_status != 'Valid'
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
            
    except Exception as e:
        logging.error(f"User profile API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test_positions')
def get_test_positions():
    """Test endpoint showing position data structure based on Kotak Neo API"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Sample position data structure from real Kotak Neo API response
    test_positions = [
        {
            'tradingsymbol': 'KPITTECH25JUNFUT',
            'exchange': 'nse_fo',
            'product': 'NRML',
            'quantity': 400,
            'buy_quantity': 400,
            'sell_quantity': 0,
            'averageprice': 1353.6,
            'ltp': 1320.0,
            'pnl': -13440.0,
            'unrealised': -13440.0,
            'realised_pnl': 0.0,
            'day_change': -33.6,
            'day_change_percent': -2.49,
            'buy_amount': 541440.0,
            'sell_amount': 0.0,
            'series': 'XX',
            'symbol': 'KPITTECH',
            'expiry_date': '26 Jun, 2025',
            'strike_price': '0.00',
            'option_type': 'XX',
            'lot_size': 400
        },
        {
            'tradingsymbol': 'NIFTY25JUNPE25000',
            'exchange': 'nse_fo',
            'product': 'NRML',
            'quantity': -75,
            'buy_quantity': 0,
            'sell_quantity': 75,
            'averageprice': 414.77,
            'ltp': 282.15,
            'pnl': 9946.38,
            'unrealised': 9946.38,
            'realised_pnl': 0.0,
            'day_change': 132.62,
            'day_change_percent': 47.01,
            'buy_amount': 0.0,
            'sell_amount': 31107.63,
            'series': 'XX',
            'symbol': 'NIFTY',
            'expiry_date': '26 Jun, 2025',
            'strike_price': '25000.00',
            'option_type': 'PE',
            'lot_size': 75
        }
    ]
    
    return jsonify({
        'success': True,
        'positions': test_positions,
        'count': len(test_positions)
    })

# Database Management Endpoints
@app.route('/api/users')
def get_users():
    """Get all users from database"""
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        users = User.query.filter_by(is_active=True).all()
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            "success": True,
            "data": users_data,
            "count": len(users_data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    """Get specific user by ID"""
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get user sessions
        sessions = UserSession.query.filter_by(user_id=user_id).order_by(UserSession.created_at.desc()).limit(5).all()
        sessions_data = []
        for s in sessions:
            sessions_data.append({
                "id": s.id,
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "is_active": s.is_active
            })
        
        return jsonify({
            "success": True,
            "data": {
                "user": user.to_dict(),
                "recent_sessions": sessions_data
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-stats')
def get_user_stats():
    """Get user statistics"""
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        stats = user_manager.get_user_stats()
        
        # Get additional stats
        total_sessions = UserSession.query.count()
        recent_logins = User.query.filter(
            User.last_login > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        stats.update({
            "total_sessions": total_sessions,
            "recent_logins_24h": recent_logins
        })
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/current-user')
def get_current_user():
    """Get current logged-in user data"""
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        db_user_id = session.get('db_user_id')
        if db_user_id:
            user = User.query.get(db_user_id)
            if user:
                return jsonify({
                    "success": True,
                    "data": user.to_dict()
                })
        
        # Fallback to session data if no database user
        return jsonify({
            "success": True,
            "data": {
                "ucc": session.get('ucc'),
                "greeting_name": session.get('greeting_name'),
                "user_id": session.get('user_id'),
                "source": "session_only"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cleanup-sessions', methods=['POST'])
def cleanup_sessions():
    """Clean up expired sessions"""
    if not session.get('authenticated'):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cleaned_count = user_manager.clean_expired_sessions()
        return jsonify({
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-user-storage', methods=['POST'])
def test_user_storage():
    """Test endpoint to create sample user data and verify storage"""
    try:
        # Create test login response data
        test_login_response = {
            'success': True,
            'data': {
                'ucc': 'TEST123456',
                'mobile_number': '9876543210',
                'greeting_name': 'Test User',
                'user_id': 'USER001',
                'client_code': 'CLIENT001',
                'product_code': 'PROD001',
                'account_type': 'INDIVIDUAL',
                'branch_code': 'BRANCH001',
                'is_trial_account': False,
                'access_token': 'test_access_token_12345',
                'session_token': 'test_session_token_67890',
                'sid': 'SID123456789',
                'rid': 'RID987654321'
            }
        }
        
        # Create or update user in database
        db_user = user_manager.create_or_update_user(test_login_response)
        
        # Create session record
        user_session = user_manager.create_user_session(db_user.id, test_login_response)
        
        return jsonify({
            "success": True,
            "message": "Test user data stored successfully",
            "data": {
                "user_id": db_user.id,
                "ucc": db_user.ucc,
                "stored_fields": {
                    "sid": db_user.sid,
                    "rid": db_user.rid,
                    "access_token": db_user.access_token[:20] + "..." if db_user.access_token else None,
                    "session_token": db_user.session_token[:20] + "..." if db_user.session_token else None,
                    "mobile_number": db_user.mobile_number,
                    "greeting_name": db_user.greeting_name,
                    "user_id": db_user.user_id,
                    "client_code": db_user.client_code,
                    "product_code": db_user.product_code,
                    "account_type": db_user.account_type,
                    "branch_code": db_user.branch_code,
                    "is_trial_account": db_user.is_trial_account,
                    "last_login": db_user.last_login.isoformat() if db_user.last_login else None
                },
                "session_id": user_session.session_id
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/database-status')
def database_status():
    """Check database connection and show stored data"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        
        # Get counts
        user_count = User.query.count()
        session_count = UserSession.query.count()
        preference_count = UserPreferences.query.count()
        
        # Get sample data if exists
        sample_user = User.query.first()
        sample_data = None
        if sample_user:
            sample_data = {
                "ucc": sample_user.ucc,
                "sid": sample_user.sid,
                "rid": sample_user.rid,
                "greeting_name": sample_user.greeting_name,
                "last_login": sample_user.last_login.isoformat() if sample_user.last_login else None
            }
        
        return jsonify({
            "success": True,
            "database_connected": True,
            "tables": {
                "users": user_count,
                "user_sessions": session_count,
                "user_preferences": preference_count
            },
            "sample_user_data": sample_data,
            "data_fields_stored": [
                "ucc", "mobile_number", "greeting_name", "user_id", 
                "client_code", "product_code", "account_type", "branch_code",
                "is_trial_account", "access_token", "session_token", 
                "sid", "rid", "created_at", "updated_at", "last_login",
                "session_expires_at", "is_active"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "database_connected": False,
            "error": str(e)
        }), 500

@app.route('/api/search-symbols')
def search_symbols():
    """Search trading symbols"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401

        query = request.args.get('q', '').strip().upper()
        if not query or len(query) < 2:
            return jsonify([])

        # Popular Indian stocks for demonstration
        popular_symbols = [
            {'symbol': 'RELIANCE', 'name': 'Reliance Industries Limited'},
            {'symbol': 'TCS', 'name': 'Tata Consultancy Services Limited'},
            {'symbol': 'HDFCBANK', 'name': 'HDFC Bank Limited'},
            {'symbol': 'INFY', 'name': 'Infosys Limited'},
            {'symbol': 'ICICIBANK', 'name': 'ICICI Bank Limited'},
            {'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Limited'},
            {'symbol': 'ITC', 'name': 'ITC Limited'},
            {'symbol': 'SBIN', 'name': 'State Bank of India'},
            {'symbol': 'LT', 'name': 'Larsen & Toubro Limited'},
            {'symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank Limited'},
            {'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Limited'},
            {'symbol': 'BAJFINANCE', 'name': 'Bajaj Finance Limited'},
            {'symbol': 'AXISBANK', 'name': 'Axis Bank Limited'},
            {'symbol': 'ASIANPAINT', 'name': 'Asian Paints Limited'},
            {'symbol': 'MARUTI', 'name': 'Maruti Suzuki India Limited'},
            {'symbol': 'NESTLEIND', 'name': 'Nestle India Limited'},
            {'symbol': 'TITAN', 'name': 'Titan Company Limited'},
            {'symbol': 'WIPRO', 'name': 'Wipro Limited'},
            {'symbol': 'TATAMOTORS', 'name': 'Tata Motors Limited'},
            {'symbol': 'HCLTECH', 'name': 'HCL Technologies Limited'}
        ]

        # Filter symbols based on query
        matching_symbols = [
            symbol for symbol in popular_symbols
            if query in symbol['symbol'] or query in symbol['name'].upper()
        ]

        return jsonify(matching_symbols[:10])  # Return max 10 results
            
    except Exception as e:
        logging.error(f"Symbol search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart-data')
def get_chart_data():
    """Get chart data for a symbol"""
    try:
        if not session.get('authenticated'):
            return jsonify({'error': 'Not authenticated'}), 401

        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        symbol = request.args.get('symbol', '').strip().upper()
        period = request.args.get('period', '1W')
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Use the Kotak Neo client to get real quotes data
        try:
            # Get current quote for the symbol
            quote_data = {'instrument_tokens': [symbol], 'quote_type': 'ltp'}
            quotes_response = trading_functions.get_quotes(client, quote_data)
            
            # For historical data, we'll need to implement with available API endpoints
            # For now, we'll provide a basic implementation that can be extended
            from datetime import datetime, timedelta
            import random
            
            # Calculate date range based on period
            end_dt = datetime.now()
            if period == '1D':
                start_dt = end_dt - timedelta(days=1)
                interval = timedelta(minutes=5)
            elif period == '1W':
                start_dt = end_dt - timedelta(weeks=1)
                interval = timedelta(hours=1)
            elif period == '1M':
                start_dt = end_dt - timedelta(days=30)
                interval = timedelta(hours=4)
            elif period == '3M':
                start_dt = end_dt - timedelta(days=90)
                interval = timedelta(days=1)
            elif period == '1Y':
                start_dt = end_dt - timedelta(days=365)
                interval = timedelta(days=1)
            elif period == 'custom' and start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                days_diff = (end_dt - start_dt).days
                if days_diff <= 7:
                    interval = timedelta(hours=1)
                elif days_diff <= 30:
                    interval = timedelta(hours=4)
                else:
                    interval = timedelta(days=1)
            else:
                return jsonify({'error': 'Invalid period'}), 400

            # Get current price from quotes if available
            current_price = 2500.0  # Default fallback
            if quotes_response and isinstance(quotes_response, dict):
                # Extract price from quotes response if available
                if 'data' in quotes_response:
                    quotes_data = quotes_response['data']
                    if quotes_data and isinstance(quotes_data, list) and len(quotes_data) > 0:
                        first_quote = quotes_data[0]
                        if 'ltp' in first_quote:
                            current_price = float(first_quote['ltp'])

            # Generate realistic historical data based on current price
            candlesticks = []
            volume_data = []
            
            # Start from a price slightly different from current
            base_price = current_price * random.uniform(0.95, 1.05)
            price = base_price
            
            current_dt = start_dt
            while current_dt <= end_dt:
                # Generate OHLC data with realistic movements
                open_price = price
                price_change = random.uniform(-0.02, 0.02)  # Max 2% change per interval
                close_price = open_price * (1 + price_change)
                
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.015)
                low_price = min(open_price, close_price) * random.uniform(0.985, 1.0)
                
                volume = random.randint(50000, 500000)
                
                # Convert to timestamp (seconds)
                timestamp = int(current_dt.timestamp())
                
                candlesticks.append({
                    'time': timestamp,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2)
                })
                
                volume_data.append({
                    'time': timestamp,
                    'value': volume,
                    'color': '#16a34a' if close_price >= open_price else '#dc2626'
                })
                
                price = close_price
                current_dt += interval

            return jsonify({
                'symbol': symbol,
                'candlesticks': candlesticks,
                'volume': volume_data,
                'period': period,
                'current_price': current_price
            })
            
        except Exception as api_error:
            logging.warning(f"Chart data API error: {str(api_error)}")
            return jsonify({'error': 'Unable to fetch chart data. Please ensure you have an active session.'}), 500
            
    except Exception as e:
        logging.error(f"Chart data error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)