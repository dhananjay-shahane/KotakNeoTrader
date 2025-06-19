
"""ETF Trading Signals API endpoints"""
from flask import request, jsonify, session, Blueprint
from app import db
from etf_trading_signals import ETFTradingSignals
from user_manager import UserManager
from models_etf import ETFSignalTrade
import logging
from datetime import datetime

etf_bp = Blueprint('etf', __name__, url_prefix='/etf')
logger = logging.getLogger(__name__)

@etf_bp.route('/positions', methods=['GET'])
def get_etf_positions():
    """Get ETF positions/trades for current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get current user from database
        from models import User
        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get ETF signal trades for current user
        trades = ETFSignalTrade.query.filter_by(user_id=current_user.id).order_by(ETFSignalTrade.created_at.desc()).all()

        # Calculate portfolio summary
        total_invested = 0
        current_value = 0
        total_pnl = 0
        profit_trades = 0
        loss_trades = 0

        trades_data = []
        for trade in trades:
            trade_dict = trade.to_dict()
            trades_data.append(trade_dict)

            # Update calculations
            if trade.invested_amount:
                total_invested += float(trade.invested_amount)
            if trade.current_value:
                current_value += float(trade.current_value)
            if trade.pnl_amount:
                pnl = float(trade.pnl_amount)
                total_pnl += pnl
                if pnl > 0:
                    profit_trades += 1
                elif pnl < 0:
                    loss_trades += 1

        # Calculate return percentage
        return_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        portfolio_summary = {
            'total_invested': total_invested,
            'current_value': current_value,
            'total_pnl': total_pnl,
            'return_percent': return_percent,
            'profit_trades': profit_trades,
            'loss_trades': loss_trades,
            'total_trades': len(trades_data)
        }

        return jsonify({
            'success': True,
            'trades': trades_data,
            'portfolio': portfolio_summary
        })

    except Exception as e:
        logging.error(f"Error fetching ETF positions: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching data: {str(e)}'}), 500

@etf_bp.route('/user-deals', methods=['GET'])
def get_user_deals():
    """Get deals created by current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        from models import User
        from models_etf import UserDeal

        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get user deals
        deals = UserDeal.query.filter_by(user_id=current_user.id).order_by(UserDeal.created_at.desc()).all()

        deals_data = []
        total_invested = 0
        total_current_value = 0

        for deal in deals:
            deal_dict = deal.to_dict()
            deals_data.append(deal_dict)

            if deal.invested_amount:
                total_invested += float(deal.invested_amount)
            if deal.current_value:
                total_current_value += float(deal.current_value)

        summary = {
            'total_deals': len(deals_data),
            'total_invested': total_invested,
            'total_current_value': total_current_value,
            'total_pnl': total_current_value - total_invested
        }

        return jsonify({
            'success': True,
            'deals': deals_data,
            'summary': summary
        })

    except Exception as e:
        logging.error(f"Error fetching user deals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching deals: {str(e)}'}), 500

@etf_bp.route('/create-deal', methods=['POST'])
def create_deal():
    """Create a new deal from signal or manually"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        from models import User
        from models_etf import UserDeal, ETFSignalTrade

        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        data = request.get_json()

        # Validate required fields
        required_fields = ['symbol', 'position_type', 'quantity', 'entry_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Calculate invested amount
        invested_amount = float(data['entry_price']) * int(data['quantity'])

        # Create deal
        deal = UserDeal(
            user_id=current_user.id,
            signal_id=data.get('signal_id'),
            symbol=data['symbol'].upper(),
            trading_symbol=data.get('trading_symbol', f"{data['symbol'].upper()}-EQ"),
            exchange=data.get('exchange', 'NSE'),
            position_type=data['position_type'].upper(),
            quantity=int(data['quantity']),
            entry_price=float(data['entry_price']),
            current_price=float(data.get('current_price', data['entry_price'])),
            target_price=float(data['target_price']) if data.get('target_price') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            invested_amount=invested_amount,
            current_value=invested_amount,
            deal_type=data.get('deal_type', 'MANUAL'),
            notes=data.get('notes')
        )

        # Calculate initial P&L
        deal.calculate_pnl()

        db.session.add(deal)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Deal created successfully',
            'deal_id': deal.id
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating deal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating deal: {str(e)}'}), 500

@etf_bp.route('/add-position', methods=['POST'])
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

@etf_bp.route('/update-position', methods=['PUT'])
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

@etf_bp.route('/delete-position', methods=['DELETE'])
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

@etf_bp.route('/search-instruments', methods=['GET'])
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

@etf_bp.route('/quotes', methods=['POST'])
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

@etf_bp.route('/portfolio-summary', methods=['GET'])
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

@etf_bp.route('/bulk-update', methods=['PUT'])
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

@etf_bp.route('/signal-trades', methods=['GET'])
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

@etf_bp.route('/update-signal-trade', methods=['PUT'])
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
