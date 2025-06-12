"""Trading API endpoints"""
from flask import Blueprint, request, jsonify, session
import logging

from utils.auth import login_required
from trading_functions import TradingFunctions

trading_api = Blueprint('trading_api', __name__)
trading_functions = TradingFunctions()

@trading_api.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Place a new order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.place_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Place order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/modify_order', methods=['POST'])
@login_required
def modify_order():
    """Modify an existing order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.modify_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Modify order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/cancel_order', methods=['POST'])
@login_required
def cancel_order():
    """Cancel an existing order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.cancel_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Cancel order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/get_quotes')
@login_required
def get_quotes():
    """API endpoint to get live quotes"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        quote_data = {
            'instrument_tokens': request.args.getlist('tokens'),
            'quote_type': request.args.get('type', 'ltp')
        }
        result = trading_functions.get_quotes(client, quote_data)
        return jsonify(result)

    except Exception as e:
        logging.error(f"Get quotes error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trading_api.route('/search-symbols')
@login_required
def search_symbols():
    """Search trading symbols"""
    try:
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

        return jsonify(matching_symbols[:10])

    except Exception as e:
        logging.error(f"Symbol search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trading_api.route('/chart-data')
@login_required
def get_chart_data():
    """Get chart data for a symbol"""
    try:
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
            quote_data = {'instrument_tokens': [symbol], 'quote_type': 'ltp'}
            quotes_response = trading_functions.get_quotes(client, quote_data)

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
                if 'data' in quotes_response:
                    quotes_data = quotes_response['data']
                    if quotes_data and isinstance(quotes_data, list) and len(quotes_data) > 0:
                        first_quote = quotes_data[0]
                        if 'ltp' in first_quote:
                            current_price = float(first_quote['ltp'])

            # Generate realistic historical data based on current price
            candlesticks = []
            volume_data = []

            base_price = current_price * random.uniform(0.95, 1.05)
            price = base_price

            current_dt = start_dt
            while current_dt <= end_dt:
                open_price = price
                price_change = random.uniform(-0.02, 0.02)
                close_price = open_price * (1 + price_change)

                high_price = max(open_price, close_price) * random.uniform(1.0, 1.015)
                low_price = min(open_price, close_price) * random.uniform(0.985, 1.0)

                volume = random.randint(50000, 500000)

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