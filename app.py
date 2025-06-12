import os

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
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

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
    """Validate current session without auto-login bypass"""
    try:
        if not session.get('authenticated'):
            return False
            
        access_token = session.get('access_token')
        if not access_token:
            return False
            
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
            
        if neo_client.validate_session(client):
            return True
        else:
            session.clear()
            return False
            
    except Exception as e:
        logging.error(f"Session validation error: {e}")
        return False

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
    if request.method == 'POST':
        try:
            mobile_number = request.form.get('mobile_number')
            ucc = request.form.get('ucc')
            totp = request.form.get('totp')
            mpin = request.form.get('mpin')
            demo_mode = request.form.get('demo_mode')
            
            # Demo mode for testing
            if demo_mode == 'true':
                session['authenticated'] = True
                session['demo_mode'] = True
                session['access_token'] = 'demo_token'
                session['session_token'] = 'demo_session'
                session['sid'] = 'demo_sid'
                session['user_data'] = {
                    'ucc': 'DEMO123',
                    'greetingName': 'Demo User',
                    'isTrialAccount': True
                }
                flash('Demo mode activated!', 'info')
                return redirect(url_for('dashboard'))
            
            if not all([mobile_number, ucc, totp, mpin]):
                flash('All fields are required', 'error')
                return render_template('login.html')
            
            # Execute TOTP login
            login_response = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)
            
            if login_response and login_response.get('data'):
                # Store session data
                session['authenticated'] = True
                session['access_token'] = login_response.get('data', {}).get('token')
                session['session_token'] = login_response.get('data', {}).get('sid')
                session['sid'] = login_response.get('data', {}).get('sid')
                session['user_data'] = login_response.get('data', {})
                
                # Store user in database
                user = user_manager.create_or_update_user(login_response)
                if user:
                    user_manager.create_user_session(user.id, login_response)
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Handle specific error cases
                if login_response and login_response.get('error'):
                    errors = login_response.get('error', [])
                    if errors and isinstance(errors, list):
                        error_msg = errors[0].get('message', 'Login failed')
                        # Check for account lock
                        if 'locked' in error_msg.lower():
                            flash(f'Account Error: {error_msg}. Please try again tomorrow or contact support.', 'error')
                        else:
                            flash(f'Login Error: {error_msg}', 'error')
                    else:
                        flash('Login failed. Please check your credentials.', 'error')
                else:
                    error_msg = login_response.get('emsg', 'Login failed') if login_response else 'Login failed'
                    flash(f'Login failed: {error_msg}', 'error')
                
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash('Login failed due to technical error', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with portfolio overview"""
    if not validate_current_session():
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/positions')
def positions():
    """Positions page"""
    if not validate_current_session():
        return redirect(url_for('login'))
    
    return render_template('positions.html')

@app.route('/holdings')
def holdings():
    """Holdings page"""
    if not validate_current_session():
        return redirect(url_for('login'))
    
    return render_template('holdings.html')

@app.route('/orders')
def orders():
    """Orders page"""
    if not validate_current_session():
        return redirect(url_for('login'))
    
    return render_template('orders.html')

@app.route('/charts')
def charts():
    """Charts page for trading analysis"""
    if not validate_current_session():
        return redirect(url_for('login'))
    
    return render_template('charts.html')

# API endpoints
@app.route('/api/dashboard-data')
def get_dashboard_data_api():
    """AJAX endpoint for dashboard data without page refresh"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Handle demo mode
        if session.get('demo_mode'):
            return jsonify({
                'portfolio_value': 125000.50,
                'day_pnl': 2350.25,
                'total_pnl': 15420.75,
                'available_margin': 45000.00,
                'positions': [],
                'holdings': [],
                'orders': []
            })
            
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
        # Handle demo mode
        if session.get('demo_mode'):
            return jsonify([])
            
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
        # Handle demo mode
        if session.get('demo_mode'):
            return jsonify([])
            
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400
            
        holdings = trading_functions.get_holdings(client)
        return jsonify(holdings)
    except Exception as e:
        logging.error(f"Holdings API error: {e}")
        return jsonify({'error': str(e)}), 500