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
            # Check if tokens are provided directly
            access_token = request.form.get('access_token')
            session_token = request.form.get('session_token')

            if access_token and session_token:
                # Direct token login
                client = neo_client.initialize_client_with_tokens(
                    access_token=access_token,
                    session_token=session_token,
                    sid=request.form.get('sid')
                )

                if client:
                    session['authenticated'] = True
                    session['client'] = client
                    session['credentials'] = {
                        'access_token': access_token,
                        'session_token': session_token,
                        'sid': request.form.get('sid', ''),
                        'ucc': request.form.get('ucc', 'ZHZ3J')
                    }
                    session.permanent = True
                    flash('Login successful with tokens!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Failed to initialize client with tokens', 'error')
            else:
                # Traditional TOTP login
                mobile_number = request.form.get('mobile_number')
                ucc = request.form.get('ucc')
                mpin = request.form.get('mpin')
                totp = request.form.get('totp')

                # Validate required fields
                if not all([mobile_number, ucc, mpin, totp]):
                    flash('All fields are required for TOTP login', 'error')
                    return render_template('login.html')

                # Store credentials in session for API initialization
                session['credentials'] = {
                    'mobile_number': mobile_number,
                    'ucc': ucc,
                    'mpin': mpin,
                    'consumer_key': os.environ.get('KOTAK_CONSUMER_KEY', ''),
                    'consumer_secret': os.environ.get('KOTAK_CONSUMER_SECRET', ''),
                    'neo_fin_key': os.environ.get('KOTAK_NEO_FIN_KEY', 'neotradeapi')
                }

                # Initialize Neo API client
                client = neo_client.initialize_client(session['credentials'])
                if not client:
                    flash('Failed to initialize API client', 'error')
                    return render_template('login.html')

                # Perform TOTP login
                success = neo_client.login_with_totp(client, mobile_number, ucc, totp, mpin)
                if success:
                    session['authenticated'] = True
                    session['client'] = client
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Login failed. Please check your credentials and TOTP code.', 'error')

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login error: {str(e)}', 'error')

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
        if 'credentials' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'})

        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'})

        # Get comprehensive portfolio summary
        result = trading_functions.get_portfolio_summary(client)
        
        if result['success']:
            summary_data = result['data']['summary']
            return jsonify({
                'success': True,
                'total_positions': summary_data['positions_count'],
                'total_holdings': summary_data['holdings_count'],
                'total_orders': len(trading_functions.get_orders(client)),
                'total_pnl': summary_data['total_pnl'],
                'total_investment': summary_data['total_investment'],
                'day_change': summary_data['day_change'],
                'limits_available': summary_data['limits_available']
            })
        else:
            return jsonify(result)
            
    except Exception as e:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)