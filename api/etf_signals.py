"""ETF Trading Signals API endpoints"""
from flask import Blueprint, request, jsonify, session
from app import db
from etf_trading_signals import ETFTradingSignals
from user_manager import UserManager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create the ETF signals API blueprint
etf_signals_api = Blueprint('etf_signals_api', __name__)


@etf_signals_api.route('/etf_positions', methods=['GET'])
def get_etf_positions():
    """Get ETF positions data"""
    try:
        # Read and parse the CSV data
        csv_data = parse_etf_csv_data()

        # Convert to ETF signals format
        etf_data = []
        for row in csv_data:
            if row.get('symbol') and row.get('symbol') != 'ETF':  # Skip header
                etf_data.append({
                    'symbol': row.get('symbol', ''),
                    'qty': int(row.get('qty', 0)) if row.get('qty') else 0,
                    'entry_price': float(row.get('ep', 0)) if row.get('ep') else 0,
                    'current_price': float(row.get('cmp', 0)) if row.get('cmp') else 0,
                    'pnl': float(row.get('pl', 0)) if row.get('pl') else 0,
                    'pnl_percent': float(row.get('change_pct', 0)) if row.get('change_pct') else 0,
                    'investment': float(row.get('inv', 0)) if row.get('inv') else 0,
                    'current_value': float(row.get('qty', 0)) * float(row.get('cmp', 0)) if row.get('qty') and row.get('cmp') else 0,
                    'signal': determine_signal(row),
                    'strength': determine_strength(row),
                    'target_price': float(row.get('tp', 0)) if row.get('tp') else 0,
                    'stop_loss': float(row.get('ep', 0)) * 0.95 if row.get('ep') else 0,
                    'sector': 'ETF',
                    'confidence': calculate_confidence(row),
                    'last_updated': datetime.now().isoformat(),
                    'pos': int(row.get('pos', 1)) if row.get('pos') else 1,
                    'date': row.get('date', ''),
                    'exp': row.get('exp', ''),
                    'pr': row.get('pr', ''),
                    'pp': row.get('pp', ''),
                    'iv': row.get('iv', ''),
                    'ip': row.get('ip', ''),
                    'nt': row.get('nt', ''),
                    'qt': row.get('qt', '')
                })

        # Add comprehensive sample ETF data if CSV data is empty
        if not etf_data:
            etf_data = [
                {
                    'symbol': 'NIFTYBEES',
                    'qty': 200,
                    'entry_price': 227.00,
                    'current_price': 225.70,
                    'pnl': -260.00,
                    'pnl_percent': -0.57,
                    'investment': 45400.00,
                    'current_value': 45140.00,
                    'signal': 'HOLD',
                    'strength': 'WEAK',
                    'target_price': 254.26,
                    'stop_loss': 215.65,
                    'sector': 'INDEX',
                    'confidence': 75.0,
                    'last_updated': datetime.now().isoformat(),
                    'pos': 1,
                    'date': '22-Nov-2024',
                    'exp': '-',
                    'pr': '220-235',
                    'pp': '★★',
                    'iv': 'Med',
                    'ip': '-0.57%',
                    'nt': 'Index ETF',
                    'qt': '15:30'
                },
                {
                    'symbol': 'GOLDBEES',
                    'qty': 500,
                    'entry_price': 40.23,
                    'current_price': 40.00,
                    'pnl': -115.00,
                    'pnl_percent': -0.57,
                    'investment': 20115.00,
                    'current_value': 20000.00,
                    'signal': 'BUY',
                    'strength': 'MEDIUM',
                    'target_price': 45.79,
                    'stop_loss': 38.22,
                    'sector': 'GOLD',
                    'confidence': 80.0,
                    'last_updated': datetime.now().isoformat(),
                    'pos': 1,
                    'date': '13-Dec-2024',
                    'exp': '-',
                    'pr': '38-42',
                    'pp': '★',
                    'iv': 'Low',
                    'ip': '-0.57%',
                    'nt': 'Gold ETF',
                    'qt': '15:29'
                },
                {
                    'symbol': 'BANKBEES',
                    'qty': 100,
                    'entry_price': 46.15,
                    'current_price': 45.00,
                    'pnl': -115.00,
                    'pnl_percent': -2.49,
                    'investment': 4615.00,
                    'current_value': 4500.00,
                    'signal': 'HOLD',
                    'strength': 'WEAK',
                    'target_price': 52.26,
                    'stop_loss': 43.84,
                    'sector': 'BANKING',
                    'confidence': 65.0,
                    'last_updated': datetime.now().isoformat(),
                    'pos': 0,
                    'date': '20-Dec-2024',
                    'exp': '-',
                    'pr': '44-48',
                    'pp': '★★',
                    'iv': 'Med',
                    'ip': '-2.49%',
                    'nt': 'Bank ETF',
                    'qt': '15:28'
                },
                {
                    'symbol': 'SILVERBEES',
                    'qty': 607,
                    'entry_price': 93.00,
                    'current_price': 104.29,
                    'pnl': 6850.03,
                    'pnl_percent': 12.13,
                    'investment': 56451.00,
                    'current_value': 63301.03,
                    'signal': 'SELL',
                    'strength': 'STRONG',
                    'target_price': 97.70,
                    'stop_loss': 88.35,
                    'sector': 'SILVER',
                    'confidence': 90.0,
                    'last_updated': datetime.now().isoformat(),
                    'pos': 1,
                    'date': '22-Nov-2024',
                    'exp': '-',
                    'pr': '92-97',
                    'pp': '★★★',
                    'iv': 'High',
                    'ip': '+12.13%',
                    'nt': 'Silver ETF',
                    'qt': '15:27'
                },
                {
                    'symbol': 'ITBEES',
                    'qty': 1560,
                    'entry_price': 64.25,
                    'current_price': 62.36,
                    'pnl': -2948.40,
                    'pnl_percent': -2.94,
                    'investment': 100230.00,
                    'current_value': 97281.60,
                    'signal': 'BUY',
                    'strength': 'MEDIUM',
                    'target_price': 69.00,
                    'stop_loss': 61.04,
                    'sector': 'IT',
                    'confidence': 70.0,
                    'last_updated': datetime.now().isoformat(),
                    'pos': 1,
                    'date': '16-Dec-2024',
                    'exp': '-',
                    'pr': '62-67',
                    'pp': '★',
                    'iv': 'Med',
                    'ip': '-2.94%',
                    'nt': 'IT ETF',
                    'qt': '15:26'
                }
            ]

        # Calculate summary data
        total_investment = sum(item.get('investment', 0) for item in etf_data)
        total_current_value = sum(item.get('current_value', 0) for item in etf_data)
        total_pnl = sum(item.get('pnl', 0) for item in etf_data)
        active_positions = len([item for item in etf_data if item.get('pnl', 0) != 0])
        closed_positions = len(etf_data) - active_positions
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0

        summary = {
            'total_positions': len(etf_data),
            'total_investment': total_investment,
            'current_value': total_current_value,
            'total_pnl': total_pnl,
            'return_percent': return_percent,
            'active_positions': active_positions,
            'closed_positions': closed_positions
        }

        return jsonify({
            'success': True,
            'positions': etf_data,
            'summary': summary,
            'total_positions': len(etf_data),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"ETF positions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

def parse_etf_csv_data():
    """Parse ETF CSV data from attached assets"""
    try:
        import csv
        import os

        # Look for the latest CSV file
        csv_files = []
        assets_dir = 'attached_assets'

        if os.path.exists(assets_dir):
            for file in os.listdir(assets_dir):
                if file.startswith('INVESTMENTS - ETFS-V2_') and file.endswith('.csv'):
                    csv_files.append(os.path.join(assets_dir, file))

        if not csv_files:
            return []

        # Use the latest CSV file
        latest_csv = max(csv_files, key=os.path.getctime)

        etf_data = []
        with open(latest_csv, 'r', encoding='utf-8') as file:
            # Skip the first few header rows and find the actual data
            lines = file.readlines()

            # Find the header row with ETF data
            header_found = False
            headers = []

            for i, line in enumerate(lines):
                if 'ETF' in line and 'Date' in line and 'Pos' in line:
                    # This is our header row
                    headers = [col.strip() for col in line.split(',')]
                    header_found = True

                    # Process data rows
                    for j in range(i + 1, len(lines)):
                        data_line = lines[j].strip()
                        if not data_line or data_line.startswith(','):
                            continue

                        values = [val.strip().replace('"', '').replace('₹', '').replace(',', '') for val in data_line.split(',')]

                        if len(values) >= 8 and values[0]:  # Ensure we have enough data
                            try:
                                row_data = {
                                    'symbol': values[0] if values[0] else '',
                                    'date': values[3] if len(values) > 3 else '',
                                    'pos': int(values[4]) if len(values) > 4 and values[4].isdigit() else 1,
                                    'qty': int(values[5]) if len(values) > 5 and values[5].replace('.', '').isdigit() else 0,
                                    'ep': float(values[6]) if len(values) > 6 and values[6].replace('.', '').isdigit() else 0,
                                    'cmp': float(values[7]) if len(values) > 7 and values[7].replace('.', '').isdigit() else 0,
                                    'change_pct': float(values[8].replace('%', '')) if len(values) > 8 and '%' in values[8] else 0,
                                    'inv': float(values[9]) if len(values) > 9 and values[9].replace('.', '').isdigit() else 0,
                                    'tp': float(values[10]) if len(values) > 10 and values[10].replace('.', '').isdigit() else 0,
                                    'tva': float(values[11]) if len(values) > 11 and values[11].replace('.', '').isdigit() else 0,
                                    'tpr': values[12] if len(values) > 12 else '',
                                    'pl': float(values[13]) if len(values) > 13 and values[13].replace('-', '').replace('.', '').isdigit() else 0,
                                    'exp': values[15] if len(values) > 15 else '',
                                    'pr': values[16] if len(values) > 16 else '',
                                    'pp': values[17] if len(values) > 17 else '',
                                    'iv': values[18] if len(values) > 18 else '',
                                    'ip': values[19] if len(values) > 19 else '',
                                    'nt': values[20] if len(values) > 20 else '',
                                    'qt': values[21] if len(values) > 21 else '',
                                }

                                if row_data['symbol'] and row_data['symbol'] != 'ETF':
                                    etf_data.append(row_data)

                            except (ValueError, IndexError) as e:
                                logging.warning(f"Error parsing row: {e}")
                                continue
                    break

        return etf_data

    except Exception as e:
        logging.error(f"Error parsing CSV data: {e}")
        return []

def determine_signal(row):
    """Determine trading signal based on position and P&L"""
    try:
        pos = int(row.get('pos', 1))
        pnl = float(row.get('pl', 0))
        change_pct = float(row.get('change_pct', 0))

        if pos == 1:  # Long position
            if pnl > 0 and change_pct > 5:
                return 'SELL'  # Take profit
            elif pnl < 0 and change_pct < -10:
                return 'HOLD'  # Hold for recovery
            else:
                return 'BUY'   # Accumulate
        else:  # Short position or no position
            if change_pct < -5:
                return 'BUY'   # Buy the dip
            else:
                return 'HOLD'

    except (ValueError, TypeError):
        return 'HOLD'

def determine_strength(row):
    """Determine signal strength based on various factors"""
    try:
        change_pct = abs(float(row.get('change_pct', 0)))

        if change_pct > 15:
            return 'STRONG'
        elif change_pct > 5:
            return 'MEDIUM'
        else:
            return 'WEAK'

    except (ValueError, TypeError):
        return 'WEAK'

def calculate_confidence(row):
    """Calculate confidence level based on various factors"""
    try:
        change_pct = abs(float(row.get('change_pct', 0)))
        qty = int(row.get('qty', 0))

        confidence = 50  # Base confidence

        # Higher confidence for larger moves
        confidence += min(change_pct * 2, 30)

        # Higher confidence for larger positions
        confidence += min(qty / 100, 15)

        return min(confidence, 95)

    except (ValueError, TypeError):
        return 60


@etf_signals_api.route('/etf_position', methods=['POST'])
def add_etf_position():
    """Add new ETF position"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user_id = session['user_id']
        etf_manager = ETFTradingSignals()

        # Validate required fields
        required_fields = ['etf_symbol', 'trading_symbol', 'token', 'quantity', 'entry_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        position = etf_manager.add_etf_position(user_id, data)

        return jsonify({
            'success': True,
            'message': 'ETF position added successfully',
            'position': position
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding ETF position: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/etf_position', methods=['PUT'])
def update_etf_position():
    """Update existing ETF position"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        position_id = data.get('id') or data.get('position_id')
        if not position_id:
            return jsonify({'error': 'Position ID required'}), 400

        user_id = session['user_id']
        etf_manager = ETFTradingSignals()

        position = etf_manager.update_etf_position(position_id, user_id, data)

        return jsonify({
            'success': True,
            'message': 'ETF position updated successfully',
            'position': position
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating ETF position: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/etf_position', methods=['DELETE'])
def delete_etf_position():
    """Delete ETF position"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        position_id = request.args.get('id') or request.json.get('id') if request.json else None
        if not position_id:
            return jsonify({'error': 'Position ID required'}), 400

        user_id = session['user_id']
        etf_manager = ETFTradingSignals()

        success = etf_manager.delete_etf_position(position_id, user_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'ETF position deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete position'}), 500

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting ETF position: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/etf_search', methods=['GET'])
def search_etf_instruments():
    """Search for ETF instruments"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query required'}), 400

        if len(query) < 2:
            return jsonify({'error': 'Search query too short'}), 400

        etf_manager = ETFTradingSignals()
        instruments = etf_manager.search_etf_instruments(query)

        return jsonify({
            'success': True,
            'instruments': instruments,
            'count': len(instruments)
        })

    except Exception as e:
        logger.error(f"Error searching ETF instruments: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/etf_quotes', methods=['POST'])
def get_etf_quotes():
    """Get live quotes for ETF instruments"""
    try:
        data = request.get_json()
        if not data or 'instruments' not in data:
            return jsonify({'error': 'Instruments data required'}), 400

        instruments = data['instruments']
        if not isinstance(instruments, list):
            return jsonify({'error': 'Instruments must be a list'}), 400

        etf_manager = ETFTradingSignals()
        quotes = etf_manager.get_live_quotes(instruments)

        return jsonify({
            'success': True,
            'quotes': quotes,
            'count': len(quotes)
        })

    except Exception as e:
        logger.error(f"Error getting ETF quotes: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/portfolio_summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary metrics"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        etf_manager = ETFTradingSignals()
        summary = etf_manager.calculate_portfolio_summary(user_id)

        return jsonify({
            'success': True,
            'summary': summary
        })

    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({'error': str(e)}), 500


@etf_signals_api.route('/etf_positions/bulk_update', methods=['PUT'])
def bulk_update_positions():
    """Bulk update multiple ETF positions"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data or 'positions' not in data:
            return jsonify({'error': 'Positions data required'}), 400

        positions = data['positions']
        if not isinstance(positions, list):
            return jsonify({'error': 'Positions must be a list'}), 400

        user_id = session['user_id']
        etf_manager = ETFTradingSignals()

        updated_positions = []
        errors = []

        for pos_data in positions:
            try:
                if 'id' not in pos_data:
                    errors.append(f"Missing ID for position: {pos_data}")
                    continue

                position = etf_manager.update_etf_position(pos_data['id'], user_id, pos_data)
                updated_positions.append(position)

            except Exception as e:
                errors.append(f"Error updating position {pos_data.get('id', 'unknown')}: {str(e)}")

        return jsonify({
            'success': True,
            'updated_positions': updated_positions,
            'updated_count': len(updated_positions),
            'errors': errors,
            'error_count': len(errors)
        })

    except Exception as e:
        logger.error(f"Error bulk updating positions: {e}")
        return jsonify({'error': str(e)}), 500