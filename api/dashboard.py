"""Dashboard API endpoints"""
from flask import Blueprint, jsonify, session
import logging

from utils.auth import login_required
from trading_functions import TradingFunctions

dashboard_api = Blueprint('dashboard_api', __name__, url_prefix='/api')

# Initialize components
trading_functions = TradingFunctions()

@dashboard_api.route('/dashboard_data')
@login_required
def get_dashboard_data_api():
    """AJAX endpoint for dashboard data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        # Get fresh dashboard data
        raw_dashboard_data = trading_functions.get_dashboard_data(client)
        
        # Ensure proper data structure
        if isinstance(raw_dashboard_data, dict):
            dashboard_data = raw_dashboard_data
            if not isinstance(dashboard_data.get('positions'), list):
                dashboard_data['positions'] = []
            if not isinstance(dashboard_data.get('holdings'), list):
                dashboard_data['holdings'] = []
        elif isinstance(raw_dashboard_data, list):
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
            dashboard_data = {
                'positions': [],
                'holdings': [],
                'limits': {},
                'recent_orders': [],
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0
            }
            
        return jsonify(dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/positions_data')
@login_required
def get_positions_data_api():
    """AJAX endpoint for positions data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        positions_data = trading_functions.get_positions(client)
        
        # Ensure proper structure
        if isinstance(positions_data, list):
            return jsonify({'positions': positions_data, 'total': len(positions_data)})
        elif isinstance(positions_data, dict) and 'data' in positions_data:
            return jsonify({'positions': positions_data['data'], 'total': len(positions_data['data'])})
        else:
            return jsonify({'positions': [], 'total': 0})

    except Exception as e:
        logging.error(f"Positions API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/holdings_data')
@login_required
def get_holdings_data_api():
    """AJAX endpoint for holdings data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        holdings_data = trading_functions.get_holdings(client)
        
        # Ensure proper structure
        if isinstance(holdings_data, list):
            return jsonify({'holdings': holdings_data, 'total': len(holdings_data)})
        elif isinstance(holdings_data, dict) and 'data' in holdings_data:
            return jsonify({'holdings': holdings_data['data'], 'total': len(holdings_data['data'])})
        else:
            return jsonify({'holdings': [], 'total': 0})

    except Exception as e:
        logging.error(f"Holdings API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/user_profile')
@login_required
def get_user_profile():
    """Get user profile information"""
    try:
        profile_data = {
            'success': True,
            'profile': {
                'ucc': session.get('ucc', 'N/A'),
                'greeting_name': session.get('ucc', 'Trader'),
                'login_time': session.get('login_time', 'Today'),
                'access_token': session.get('access_token', 'N/A')[:20] + '...' if session.get('access_token') else 'N/A',
                'session_token': session.get('session_token', 'N/A')[:20] + '...' if session.get('session_token') else 'N/A',
                'sid': session.get('sid', 'N/A')[:15] + '...' if session.get('sid') else 'N/A',
                'token_status': 'Valid' if session.get('authenticated') else 'Invalid'
            }
        }
        return jsonify(profile_data)
    except Exception as e:
        logging.error(f"User profile API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_api.route('/portfolio_summary')
@login_required
def get_portfolio_summary():
    """Get portfolio summary data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        dashboard_data = trading_functions.get_dashboard_data(client)
        
        summary = {
            'success': True,
            'total_positions': dashboard_data.get('total_positions', 0),
            'total_holdings': dashboard_data.get('total_holdings', 0),
            'total_orders': dashboard_data.get('total_orders', 0),
            'available_margin': dashboard_data.get('limits', {}).get('cash', 0) if dashboard_data.get('limits') else 0
        }
        
        return jsonify(summary)
    except Exception as e:
        logging.error(f"Portfolio summary API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_api.route('/positions')
@login_required
def get_positions():
    """Get positions data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        positions_data = trading_functions.get_positions(client)
        
        if isinstance(positions_data, list):
            return jsonify({'success': True, 'positions': positions_data})
        elif isinstance(positions_data, dict) and 'error' in positions_data:
            return jsonify({'success': False, 'error': positions_data['error']})
        else:
            return jsonify({'success': True, 'positions': []})

    except Exception as e:
        logging.error(f"Positions API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_api.route('/live_quotes')
@login_required
def get_live_quotes():
    """Get live market quotes"""
    try:
        # Return simulated quotes for now since we don't have instrument tokens
        quotes = [
            {
                'symbol': 'RELIANCE',
                'ltp': 2450.75,
                'change': 12.50,
                'changePct': 0.51
            },
            {
                'symbol': 'TCS',
                'ltp': 3675.20,
                'change': -8.30,
                'changePct': -0.23
            },
            {
                'symbol': 'INFY',
                'ltp': 1832.45,
                'change': 22.15,
                'changePct': 1.22
            },
            {
                'symbol': 'HDFCBANK',
                'ltp': 1645.80,
                'change': 5.60,
                'changePct': 0.34
            },
            {
                'symbol': 'ICICIBANK',
                'ltp': 1198.25,
                'change': -3.75,
                'changePct': -0.31
            }
        ]
        
        return jsonify({'success': True, 'quotes': quotes})
    except Exception as e:
        logging.error(f"Live quotes API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500