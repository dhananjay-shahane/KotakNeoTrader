"""ETF Trading Signals API endpoints"""
from flask import request, jsonify, session
from app import db
from etf_trading_signals import ETFTradingSignals
from user_manager import UserManager
from models_etf import ETFSignalTrade
import logging

logger = logging.getLogger(__name__)


def get_etf_positions():
    """Get ETF signal trades for current user from database"""
    try:
        # Check authentication using the same method as other endpoints
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID not found in session'}), 401
        
        # Get ETF signal trades for the current user
        trades = ETFSignalTrade.query.filter_by(user_id=user_id).order_by(ETFSignalTrade.created_at.desc()).all()
        
        # Format trades with all required columns
        formatted_positions = []
        total_investment = 0.0
        total_current_value = 0.0
        total_pnl = 0.0
        profit_positions = 0
        loss_positions = 0
        active_positions = 0
        
        for idx, trade in enumerate(trades):
            # Update P&L calculations
            trade.calculate_pnl()
            
            # Calculate values from database trade
            investment = float(trade.invested_amount) if trade.invested_amount else 0
            current_value = float(trade.current_value) if trade.current_value else 0
            pnl = float(trade.pnl_amount) if trade.pnl_amount else 0
            
            # Parse percentage change
            change_pct_str = trade.change_pct.replace('%', '') if trade.change_pct and trade.change_pct != '0.00%' else '0'
            try:
                change_pct = float(change_pct_str)
            except:
                change_pct = float(trade.pnl_percent) if trade.pnl_percent else 0
            
            # Count profit/loss positions
            if pnl > 0:
                profit_positions += 1
            elif pnl < 0:
                loss_positions += 1
                
            # Count active positions
            is_active = trade.status == 'ACTIVE'
            if is_active:
                active_positions += 1
            
            # Accumulate totals for active positions only
            if is_active:
                total_investment += investment
                total_current_value += current_value
                total_pnl += pnl
            
            # Format position data matching CSV structure
            position_data = {
                'id': trade.id,
                'etf': trade.symbol,
                'thirty': '#N/A',
                'dh': '#N/A',
                'date': trade.entry_date.strftime('%d-%b-%Y') if trade.entry_date else '',
                'pos': 1 if is_active else 0,
                'qty': trade.quantity,
                'ep': float(trade.entry_price) if trade.entry_price else 0,
                'cmp': float(trade.current_price) if trade.current_price else 0,
                'change_pct': trade.change_pct or f"{change_pct:.2f}%",
                'inv': int(investment),
                'tp': float(trade.target_price) if trade.target_price else 0,
                'tva': int(current_value),
                'tpr': trade.tp_return or f"₹{pnl:,.0f}" if pnl > 0 else '',
                'pl': int(pnl),
                'ed': trade.exit_date.strftime('%d-%b-%Y') if trade.exit_date else '',
                'exp': '',
                'pr': '',
                'pp': '',
                'iv': int(investment * 3),  # Simulated IV value
                'ip': float(trade.pnl_percent) if trade.pnl_percent else 0,
                'nt': 1,  # Simulated number of trades
                'qt': float(trade.quantity),
                'seven': '#N/A',
                'change2': '#N/A',
                
                # Status indicators
                'position_type': trade.position_type,
                'is_active': is_active,
                'trading_symbol': trade.trading_symbol or f"{trade.symbol}-EQ",
                'token': trade.token or f"40{idx:03d}",
                'exchange': trade.exchange,
                'last_update': '15:30:00',
                'trade_title': trade.trade_title,
                'trade_description': trade.trade_description,
                'priority': trade.priority,
                
                # CSS classes for styling
                'pnl_class': 'profit' if pnl > 0 else ('loss' if pnl < 0 else 'neutral'),
                'change_class': 'profit' if change_pct > 0 else ('loss' if change_pct < 0 else 'neutral')
            }
            
            formatted_positions.append(position_data)
        
        # Calculate summary statistics
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0
        
        summary = {
            'total_positions': len(formatted_positions),
            'active_positions': active_positions,
            'closed_positions': len(formatted_positions) - active_positions,
            'total_investment': round(total_investment, 2),
            'current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 2),
            'return_percent': round(return_percent, 2),
            'profit_positions': profit_positions,
            'loss_positions': loss_positions,
            'neutral_positions': len(formatted_positions) - profit_positions - loss_positions
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


def get_user_etf_signal_trades():
    """Get ETF signal trades for current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        trades = ETFSignalTrade.query.filter_by(user_id=user_id).order_by(ETFSignalTrade.created_at.desc()).all()

        return jsonify({
            'success': True,
            'trades': [trade.to_dict() for trade in trades],
            'count': len(trades)
        })

    except Exception as e:
        logger.error(f"Error getting user ETF signal trades: {e}")
        return jsonify({'error': str(e)}), 500


def update_etf_signal_trade():
    """Update ETF signal trade status"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        trade_id = data.get('trade_id')
        
        if not trade_id:
            return jsonify({'error': 'Trade ID required'}), 400

        user_id = session['user_id']
        trade = ETFSignalTrade.query.filter_by(id=trade_id, user_id=user_id).first()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404

        # Update trade fields
        if 'current_price' in data:
            trade.current_price = float(data['current_price'])
            trade.calculate_pnl()
            trade.last_price_update = datetime.utcnow()

        if 'status' in data:
            trade.status = data['status'].upper()
            if trade.status == 'CLOSED':
                trade.exit_date = datetime.utcnow()

        trade.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Trade updated successfully',
            'trade': trade.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating ETF signal trade: {e}")
        return jsonify({'error': str(e)}), 500