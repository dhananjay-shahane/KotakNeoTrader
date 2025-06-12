"""Main application routes"""
from flask import Blueprint, render_template, session, flash, redirect, url_for
import logging

from utils.auth import login_required, validate_current_session
from trading_functions import TradingFunctions
from neo_client import NeoClient

main_bp = Blueprint('main', __name__)

# Initialize components
trading_functions = TradingFunctions()
neo_client = NeoClient()

@main_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    if session.get('authenticated'):
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with portfolio overview"""
    if not validate_current_session():
        flash('Complete the 2FA process before accessing this application', 'error')
        session.clear()
        return redirect(url_for('auth.login'))

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please complete the 2FA process and login again.', 'error')
            session.clear()
            return redirect(url_for('auth.login'))

        # Try to validate session
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
                
            # Ensure all required keys exist with default values and validate data types
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])
            
            # Convert any non-list items to empty lists for safety
            if not isinstance(dashboard_data['positions'], list):
                dashboard_data['positions'] = []
            if not isinstance(dashboard_data['holdings'], list):
                dashboard_data['holdings'] = []
            if not isinstance(dashboard_data['recent_orders'], list):
                dashboard_data['recent_orders'] = []
                
            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))
            
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
                return redirect(url_for('auth.login'))
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
            return redirect(url_for('auth.login'))
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', data={})

@main_bp.route('/positions')
@login_required
def positions():
    """Positions page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        positions_data = trading_functions.get_positions(client)
        return render_template('positions.html', positions=positions_data)
    except Exception as e:
        logging.error(f"Positions error: {str(e)}")
        flash(f'Error loading positions: {str(e)}', 'error')
        return render_template('positions.html', positions=[])

@main_bp.route('/holdings')
@login_required
def holdings():
    """Holdings page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        holdings_data = trading_functions.get_holdings(client)
        return render_template('holdings.html', holdings=holdings_data)
    except Exception as e:
        logging.error(f"Holdings error: {str(e)}")
        flash(f'Error loading holdings: {str(e)}', 'error')
        return render_template('holdings.html', holdings=[])

@main_bp.route('/orders')
@login_required
def orders():
    """Orders page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        orders_data = trading_functions.get_orders(client)
        return render_template('orders.html', orders=orders_data)
    except Exception as e:
        logging.error(f"Orders error: {str(e)}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders.html', orders=[])

@main_bp.route('/charts')
@login_required
def charts():
    """Charts page for trading analysis"""
    return render_template('charts.html')