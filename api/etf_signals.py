"""ETF Trading Signals API endpoints"""
from flask import request, jsonify, session
from app import db
from etf_trading_signals import ETFTradingSignals
from user_manager import UserManager
import logging

logger = logging.getLogger(__name__)


def get_etf_positions():
    """Get ETF positions with live data and calculations"""
    try:
        # Check authentication using the same method as other endpoints
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user_id from db_user_id or fallback to 1 for demo
        user_id = session.get('db_user_id', 1)
        
        # Import here to avoid circular imports
        from models_etf import ETFPosition
        
        # Get all positions for the user
        positions = ETFPosition.query.filter_by(user_id=user_id).all()
        
        # Format positions with all required columns
        formatted_positions = []
        total_investment = 0.0
        total_current_value = 0.0
        total_pnl = 0.0
        profit_positions = 0
        loss_positions = 0
        
        for pos in positions:
            # Calculate all values
            investment = pos.investment_amount
            current_value = pos.current_value
            pnl = pos.profit_loss
            change_pct = pos.percentage_change
            
            # Count profit/loss positions
            if pnl > 0:
                profit_positions += 1
            elif pnl < 0:
                loss_positions += 1
            
            # Accumulate totals
            total_investment += investment
            total_current_value += current_value
            total_pnl += pnl
            
            # Format position data according to your specifications
            position_data = {
                'id': pos.id,
                'etf_name': pos.etf_symbol,  # ETF Name
                'symbol': pos.etf_symbol,
                'date': pos.entry_date.strftime('%d/%m/%y') if pos.entry_date else '',  # Date
                'pos': 1 if pos.is_active else 0,  # Pos (1 = active/holding, 0 = closed)
                'qty': pos.quantity,  # Qty
                'ep': float(pos.entry_price) if pos.entry_price else 0.0,  # EP (Entry Price)
                'cmp': float(pos.current_price) if pos.current_price else 0.0,  # CMP (Current Market Price)
                'change_pct': round(change_pct, 2),  # %Chan (% Change)
                'inv': round(investment, 2),  # Inv. (Invested Amount)
                'tp': float(pos.target_price) if pos.target_price else 0.0,  # TP (Target Price)
                'tva': round(pos.target_value_amount, 2),  # TVA (Target Value Amount)
                'tpr': round(pos.target_profit_return, 2),  # TPR (Target Profit Return)
                'pl': round(pnl, 2),  # PL (Profit/Loss)
                
                # Additional columns for advanced tracking
                'ed': pos.entry_date.strftime('%d/%m/%y') if pos.entry_date else '',  # ED (Entry Date)
                'exp': '',  # EXP (Expiry - not applicable for ETFs)
                'pr': round(current_value, 2),  # PR (Present Rate/Current Value)
                'pp': round(change_pct, 2),  # PP (Present Percent)
                'iv': round(investment, 2),  # IV (Investment Value)
                'ip': round(pnl, 2),  # IP (Investment Profit)
                'nt': pos.notes or '',  # NT (Notes)
                'qt': pos.quantity,  # Qt (Quantity)
                'seven': '',  # 7 (Custom field)
                'change2': round(change_pct, 2),  # %Ch (Alternative % Change)
                
                # Status indicators
                'position_type': pos.position_type,
                'is_active': pos.is_active,
                'trading_symbol': pos.trading_symbol,
                'token': pos.token,
                'exchange': pos.exchange,
                'last_update': pos.last_update_time.strftime('%H:%M:%S') if pos.last_update_time else '',
                
                # CSS classes for styling
                'pnl_class': 'profit' if pnl > 0 else ('loss' if pnl < 0 else 'neutral'),
                'change_class': 'profit' if change_pct > 0 else ('loss' if change_pct < 0 else 'neutral')
            }
            
            formatted_positions.append(position_data)
        
        # Calculate summary statistics
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0
        
        summary = {
            'total_positions': len(positions),
            'active_positions': sum(1 for pos in positions if pos.is_active),
            'closed_positions': sum(1 for pos in positions if not pos.is_active),
            'total_investment': round(total_investment, 2),
            'current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 2),
            'return_percent': round(return_percent, 2),
            'profit_positions': profit_positions,
            'loss_positions': loss_positions,
            'neutral_positions': len(positions) - profit_positions - loss_positions
        }
        
        return jsonify({
            'success': True,
            'positions': formatted_positions,
            'summary': summary,
            'count': len(formatted_positions)
        })
        
    except Exception as e:
        logger.error(f"Error getting ETF positions: {e}")
        return jsonify({'error': str(e)}), 500


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