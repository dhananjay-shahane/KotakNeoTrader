import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from neo_client import NeoClient
from trading_functions import TradingFunctions
from websocket_handler import WebSocketHandler
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kotak-neo-trading-app-secret-key")

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Initialize Neo Client and Trading Functions
neo_client = NeoClient()
trading_functions = TradingFunctions()
websocket_handler = WebSocketHandler()

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    if 'authenticated' in session and session['authenticated']:
        return redirect(url_for('dashboard'))
    return redirect(url_for('token_login'))

@app.route('/token-login')
def token_login():
    """Quick token login page"""
    return render_template('token_login.html')

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
    """Login page with token-based authentication"""
    if request.method == 'POST':
        try:
            # Get credentials from form
            access_token = request.form.get('access_token', '').strip()
            session_token = request.form.get('session_token', '').strip()
            sid = request.form.get('sid', '').strip()
            
            if not access_token or not session_token:
                flash('Access Token and Session Token are required', 'error')
                return render_template('token_login.html')
            
            # Initialize client with tokens
            client = neo_client.initialize_client_with_tokens(access_token, session_token, sid)
            
            if client:
                # Store in session
                session['authenticated'] = True
                session['access_token'] = access_token
                session['session_token'] = session_token
                session['sid'] = sid
                session['client'] = client
                
                flash('Successfully authenticated with stored tokens!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Failed to authenticate with provided tokens', 'error')
                return render_template('token_login.html')
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')
            return render_template('token_login.html')
    
    return render_template('token_login.html')

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

        session.clear()
        flash('Logged out successfully', 'success')
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")

    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with portfolio overview"""
    if not session.get('authenticated'):
        flash('Please login to access the dashboard.', 'warning')
        return redirect(url_for('token_login'))

    try:
        # Get client from session or reinitialize if needed
        client = session.get('client')
        if not client and session.get('credentials', {}).get('access_token'):
            # Reinitialize client with stored tokens
            credentials = session.get('credentials', {})
            client = neo_client.initialize_client_with_tokens(
                credentials.get('access_token'),
                credentials.get('session_token'),
                credentials.get('sid')
            )
            if client:
                session['client'] = client

        if not client:
            flash('Session expired. Please login again.', 'error')
            session.clear()
            return redirect(url_for('token_login'))

        # Fetch dashboard data
        dashboard_data = trading_functions.get_dashboard_data(client)

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
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
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)