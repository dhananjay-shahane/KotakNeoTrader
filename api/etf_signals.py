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

@etf_bp.route('/signals', methods=['GET'])
def get_admin_signals():
    """Get real admin trade signals with live CMP values from Kotak Neo"""
    try:
        from models import User
        from models_etf import AdminTradeSignal, RealtimeQuote
        from neo_client import NeoClient
        from session_manager import SessionManager

        # Get ALL admin trade signals to show all available data
        admin_signals = AdminTradeSignal.query.order_by(AdminTradeSignal.created_at.desc()).all()

        logger.info(f"Found {len(admin_signals)} admin trade signals")

        if not admin_signals:
            logger.info("No admin trade signals found in database")
            return jsonify({
                'success': True,
                'signals': [],
                'portfolio': {
                    'total_trades': 0,
                    'active_trades': 0,
                    'profit_trades': 0,
                    'loss_trades': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'total_positions': 0,
                    'total_investment': 0,
                    'current_value': 0,
                    'return_percent': 0,
                    'active_positions': 0,
                    'closed_positions': 0
                },
                'message': 'No admin trade signals found. Please add signals from admin panel.',
                'last_update': datetime.utcnow().isoformat(),
                'quotes_fetched': 0
            })

        signals_data = []
        total_invested = 0
        total_current_value = 0
        total_pnl = 0

        # Get latest quotes from realtime_quotes table
        latest_quotes = {}
        try:
            # Get the latest quote for each symbol
            from sqlalchemy import func
            subquery = db.session.query(
                RealtimeQuote.symbol,
                func.max(RealtimeQuote.timestamp).label('max_timestamp')
            ).group_by(RealtimeQuote.symbol).subquery()

            quotes_query = db.session.query(RealtimeQuote).join(
                subquery,
                db.and_(
                    RealtimeQuote.symbol == subquery.c.symbol,
                    RealtimeQuote.timestamp == subquery.c.max_timestamp
                )
            ).all()

            for quote in quotes_query:
                latest_quotes[quote.symbol] = {
                    'current_price': float(quote.current_price),
                    'change_percent': float(quote.change_percent),
                    'last_update': quote.timestamp
                }

            logger.info(f"✅ Retrieved {len(latest_quotes)} latest quotes from database")
        except Exception as quote_error:
            logger.warning(f"⚠️ Could not fetch latest quotes from database: {quote_error}")

        # Process each admin signal to match CSV format
        for signal in admin_signals:
            # Get current price from latest quotes or use current_price field
            current_price = float(signal.current_price) if signal.current_price else float(signal.entry_price)
            change_percent = float(signal.change_percent) if signal.change_percent else 0

            # Override with latest quote if available
            if signal.symbol in latest_quotes:
                current_price = latest_quotes[signal.symbol]['current_price']
                change_percent = latest_quotes[signal.symbol]['change_percent']

                # Update signal with latest price in database
                signal.current_price = current_price
                signal.change_percent = change_percent
                signal.last_update_time = datetime.utcnow()

            # Calculate values matching the CSV format
            entry_price = float(signal.entry_price)
            quantity = signal.quantity
            invested_amount = entry_price * quantity  # "Inv." column
            current_value = current_price * quantity  # Current market value

            # P&L calculations
            if signal.signal_type.upper() == 'BUY':
                pnl_amount = (current_price - entry_price) * quantity
            else:  # SELL
                pnl_amount = (entry_price - current_price) * quantity

            pnl_percent = (pnl_amount / invested_amount * 100) if invested_amount > 0 else 0

            # Target calculations
            target_price = float(signal.target_price) if signal.target_price else 0
            target_value_amount = target_price * quantity if target_price > 0 else 0  # "TVA" column
            target_profit_return = ((target_price - entry_price) / entry_price) * 100 if target_price > 0 and entry_price > 0 else 0  # "TPR" column

            # Days held calculation
            days_held = (datetime.utcnow() - signal.created_at).days if signal.created_at else 0

            # Position status (1 for active positions, 0 for closed/inactive)
            position_status = 1 if signal.status == 'ACTIVE' else 0

            # Create signal data matching CSV columns
            signal_data = {
                'id': signal.id,
                'etf': signal.symbol,  # ETF column
                'thirty': f"{pnl_percent * 1.2:.1f}",  # 30-day performance (simulated)
                'dh': str(days_held),  # DH (Days Held)
                'date': signal.created_at.strftime('%d-%b-%Y') if signal.created_at else '',  # Date
                'pos': position_status,  # Pos (Position status)
                'qty': quantity,  # Qty
                'ep': entry_price,  # EP (Entry Price)
                'cmp': current_price,  # CMP (Current Market Price)
                'change_pct': change_percent,  # %Chan (Change %)
                'inv': invested_amount,  # Inv. (Investment)
                'tp': target_price,  # TP (Target Price)
                'tva': target_value_amount,  # TVA (Target Value Amount)
                'tpr': target_profit_return,  # TPR (Target Profit Return %)
                'pl': pnl_amount,  # PL (Profit/Loss)
                'ed': signal.expires_at.strftime('%d-%b-%Y') if signal.expires_at else '',  # ED (Expiry Date)
                'exp': '',  # EXP (Expiry field - empty for now)
                'pr': f"{pnl_percent:.1f}%",  # PR (Profit Return %)
                'pp': signal.priority,  # PP (Priority)
                'iv': invested_amount,  # IV (Investment Value)
                'ip': f"{change_percent:.2f}%",  # IP (Investment Performance %)
                'nt': signal.signal_description or f"Trading signal for {signal.symbol}",  # NT (Notes)
                'qt': datetime.utcnow().strftime('%H:%M'),  # Qt (Quote time)
                'seven': f"{pnl_percent * 0.8:.1f}%",  # 7-day performance (simulated)
                'change2': change_percent,  # Alternative change field

                # Additional fields for compatibility
                'signal_type': signal.signal_type,
                'status': signal.status,
                'symbol': signal.symbol,
                'trading_symbol': signal.trading_symbol,
                'priority': signal.priority,
                'invested_amount': invested_amount,
                'current_value': current_value,
                'profit_loss': pnl_amount,
                'profit_loss_percent': pnl_percent,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'last_updated': datetime.utcnow().strftime('%H:%M:%S')
            }

            signals_data.append(signal_data)

            # Update totals for portfolio summary
            if signal.status == 'ACTIVE':
                total_invested += invested_amount
                total_current_value += current_value
                total_pnl += pnl_amount

        # Commit price updates to database
        if latest_quotes:
            try:
                db.session.commit()
                logger.info("✅ Updated signal prices in database")
            except Exception as commit_error:
                logger.warning(f"⚠️ Could not update prices: {commit_error}")
                db.session.rollback()

        # Calculate portfolio summary
        active_signals = len([s for s in signals_data if s.get('status') == 'ACTIVE'])
        profit_signals = len([s for s in signals_data if s.get('profit_loss', 0) > 0])
        loss_signals = len([s for s in signals_data if s.get('profit_loss', 0) < 0])

        portfolio_summary = {
            'total_trades': len(signals_data),
            'active_trades': active_signals,
            'profit_trades': profit_signals,
            'loss_trades': loss_signals,
            'total_invested': total_invested,
            'total_investment': total_invested,  # Add both keys for compatibility
            'total_current_value': total_current_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            'total_positions': len(signals_data),
            'current_value': total_current_value,
            'return_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            'active_positions': active_signals,
            'closed_positions': len([s for s in signals_data if s.get('status') != 'ACTIVE'])
        }

        return jsonify({
            'success': True,
            'signals': signals_data,
            'portfolio': portfolio_summary,
            'last_update': datetime.utcnow().isoformat(),
            'quotes_fetched': len(latest_quotes)
        })

    except Exception as e:
        logger.error(f"Error fetching admin trade signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching signals: {str(e)}'}), 500

@etf_bp.route('/admin/send-signal', methods=['POST'])
def send_admin_signal():
    """Admin endpoint to send trading signals to specific users"""
    try:
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get current user - try db_user_id first, fallback to user_id
        from models import User
        from models_etf import AdminTradeSignal

        user_id = session.get('db_user_id') or session.get('user_id')
        current_user = User.query.get(user_id)

        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # For now, allow any authenticated user to send signals (you can add admin check later)
        data = request.get_json()

        # Validate required fields
        required_fields = ['target_user_ids', 'symbol', 'trading_symbol', 'signal_type', 'entry_price', 'quantity', 'signal_title']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Get target users
        target_user_ids = data['target_user_ids']
        if not isinstance(target_user_ids, list):
            target_user_ids = [target_user_ids]

        signals_created = []

        for target_user_id in target_user_ids:
            # Verify target user exists
            target_user = User.query.get(target_user_id)
            if not target_user:
                continue

            # Create new signal
            signal = AdminTradeSignal(
                admin_user_id=current_user.id,
                target_user_id=target_user_id,
                symbol=data['symbol'],
                trading_symbol=data['trading_symbol'],
                token=data.get('token'),
                exchange=data.get('exchange', 'NSE'),
                signal_type=data['signal_type'],
                entry_price=data['entry_price'],
                target_price=data.get('target_price'),
                stop_loss=data.get('stop_loss'),
                quantity=data['quantity'],
                signal_title=data['signal_title'],
                signal_description=data.get('signal_description'),
                priority=data.get('priority', 'MEDIUM'),
                expires_at=data.get('expires_at')
            )

            db.session.add(signal)
            signals_created.append({
                'target_user_id': target_user_id,
                'target_user_name': target_user.greeting_name or target_user.ucc,
                'signal_id': None  # Will be set after commit
            })

        # Commit to database
        db.session.commit()

        # Update signal IDs
        for i, signal_info in enumerate(signals_created):
            signal_info['signal_id'] = signals_created[i]['signal_id']

        return jsonify({
            'success': True,
            'message': f'Signal sent to {len(signals_created)} users',
            'signals_created': signals_created
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending admin signal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending signal: {str(e)}'}), 500

@etf_bp.route('/admin/users', methods=['GET'])
def get_target_users():
    """Get list of users to send signals to"""
    try:
        # Check authentication using the same method as other endpoints
        if not session.get('authenticated') and ('db_user_id' not in session and 'user_id' not in session):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        from models import User

        # Get all active users
        users = User.query.filter(User.is_active == True).all()

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'ucc': user.ucc,
                'name': user.greeting_name or user.ucc or f"User_{user.id}",
                'mobile': user.mobile_number or 'N/A'
            })

        logging.info(f"Found {len(users_data)} active users for admin panel")

        return jsonify({
            'success': True,
            'users': users_data
        })

    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching users: {str(e)}'}), 500

@etf_bp.route('/user-deals', methods=['GET'])
def get_user_deals():
    """Get deals created by current user"""
    try:
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get current user - try db_user_id first, fallback to user_id
        from models import User
        from models_etf import UserDeal

        user_id = session.get('db_user_id') or session.get('user_id')
        current_user = User.query.get(user_id)

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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get current user - try db_user_id first, fallback to user_id
        from models import User
        from models_etf import UserDeal, ETFSignalTrade

        user_id = session.get('db_user_id') or session.get('user_id')
        current_user = User.query.get(user_id)

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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        position_id = data.get('id') or data.get('position_id')
        if not position_id:
            return jsonify({'error': 'Position ID required'}), 400

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        position_id = request.args.get('id') or request.json.get('id') if request.json else None
        if not position_id:
            return jsonify({'error': 'Position ID required'}), 400

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data or 'positions' not in data:
            return jsonify({'error': 'Positions data required'}), 400

        positions = data['positions']
        if not isinstance(positions, list):
            return jsonify({'error': 'Positions must be a list'}), 400

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session.get('db_user_id') or session.get('user_id')
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
        # Check authentication - use db_user_id which is set during login
        if 'db_user_id' not in session and 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        trade_id = data.get('trade_id')

        if not trade_id:
            return jsonify({'error': 'Trade ID required'}), 400

        user_id = session.get('db_user_id') or session.get('user_id')
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

@etf_bp.route('/datatable/admin-signals', methods=['POST'])
def get_admin_signals_datatable():
    """DataTables endpoint for admin trade signals with server-side processing"""
    try:
        from models_etf import AdminTradeSignal, RealtimeQuote
        from models import User
        from datetime import datetime
        
        # Get DataTables parameters
        draw = int(request.json.get('draw', 1))
        start = int(request.json.get('start', 0))
        length = int(request.json.get('length', 10))
        search_value = request.json.get('search', {}).get('value', '')
        
        # Base query for admin trade signals
        query = db.session.query(AdminTradeSignal).join(
            User, AdminTradeSignal.target_user_id == User.id
        )
        
        # Apply search filter if provided
        if search_value:
            search_filter = db.or_(
                AdminTradeSignal.symbol.ilike(f'%{search_value}%'),
                AdminTradeSignal.signal_type.ilike(f'%{search_value}%'),
                AdminTradeSignal.status.ilike(f'%{search_value}%'),
                User.ucc.ilike(f'%{search_value}%')
            )
            query = query.filter(search_filter)
        
        # Get total records
        records_total = AdminTradeSignal.query.count()
        records_filtered = query.count()
        
        # Apply pagination
        signals = query.offset(start).limit(length).all()
        
        # Format data for DataTables
        data = []
        for signal in signals:
            # Get latest quote for current price
            latest_quote = RealtimeQuote.query.filter_by(
                symbol=signal.symbol
            ).order_by(RealtimeQuote.timestamp.desc()).first()
            
            current_price = float(signal.current_price) if signal.current_price else float(signal.entry_price)
            if latest_quote:
                current_price = float(latest_quote.current_price)
                # Update signal with latest price
                signal.current_price = current_price
                signal.last_update_time = datetime.utcnow()
            
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            quantity = int(signal.quantity) if signal.quantity else 0
            
            # Calculate values
            invested_amount = entry_price * quantity
            current_value = current_price * quantity
            profit_loss = current_value - invested_amount
            profit_loss_percent = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            target_price = float(signal.target_price) if signal.target_price else 0
            
            # Get target user info
            target_user = User.query.get(signal.target_user_id)
            
            # Days held
            days_held = (datetime.utcnow() - signal.created_at).days if signal.created_at else 0
            
            # Format data matching ETF signals structure
            signal_data = {
                'id': signal.id,
                'etf': signal.symbol,
                'symbol': signal.symbol,
                'trading_symbol': signal.trading_symbol or f"{signal.symbol}-EQ",
                'thirty': f"{profit_loss_percent * 1.2:.1f}%",
                'dh': str(days_held),
                'date': signal.created_at.strftime('%d-%b-%Y') if signal.created_at else '',
                'pos': 1 if signal.signal_type == 'BUY' else 0,
                'qty': quantity,
                'ep': entry_price,
                'cmp': current_price,
                'change_pct': profit_loss_percent,
                'inv': invested_amount,
                'tp': target_price,
                'tva': target_price * quantity if target_price > 0 else 0,
                'tpr': ((target_price - entry_price) / entry_price) * 100 if target_price > 0 and entry_price > 0 else 0,
                'pl': profit_loss,
                'ed': signal.expires_at.strftime('%d-%b-%Y') if signal.expires_at else '',
                'exp': signal.expires_at.strftime('%d-%b-%Y') if signal.expires_at else '',
                'pr': f"{profit_loss_percent:.1f}%",
                'pp': '★★★' if signal.priority == 'HIGH' else '★★' if signal.priority == 'MEDIUM' else '★',
                'iv': invested_amount,
                'ip': f"{profit_loss_percent:.2f}%",
                'nt': signal.signal_description or f"Trading signal for {signal.symbol}",
                'qt': datetime.utcnow().strftime('%H:%M'),
                'seven': f"{profit_loss_percent * 0.8:.1f}%",
                'change2': profit_loss_percent,
                'signal_type': signal.signal_type,
                'status': signal.status,
                'priority': signal.priority,
                'target_user_ucc': target_user.ucc if target_user else 'N/A',
                'target_user_name': target_user.greeting_name if target_user else 'N/A',
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'last_updated': datetime.utcnow().strftime('%H:%M:%S')
            }
            data.append(signal_data)
        
        # Commit price updates
        try:
            db.session.commit()
        except Exception as commit_error:
            logger.warning(f"Could not update prices: {commit_error}")
            db.session.rollback()
        
        return jsonify({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in admin signals datatable: {str(e)}")
        return jsonify({
            'draw': int(request.json.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        }), 500

@etf_bp.route('/api/etf-signals-data')
def get_etf_signals_data():
    """API endpoint to get ETF signals data from admin_trade_signals table"""
    try:
        from models_etf import AdminTradeSignal, RealtimeQuote
        from models import User
        from datetime import datetime
        
        # Get all admin trade signals
        signals = AdminTradeSignal.query.order_by(AdminTradeSignal.created_at.desc()).all()
        
        logger.info(f"ETF Signals API: Found {len(signals)} admin trade signals")
        
        if not signals:
            logger.info("ETF Signals API: No signals found, returning empty response")
            return jsonify({
                'success': True,
                'signals': [],
                'total': 0,
                'portfolio': {
                    'total_positions': 0,
                    'total_investment': 0,
                    'current_value': 0,
                    'total_pnl': 0,
                    'return_percent': 0,
                    'active_positions': 0,
                    'closed_positions': 0
                },
                'message': 'No admin trade signals found'
            })
        
        signals_data = []
        total_invested = 0
        total_current_value = 0
        total_pnl = 0
        
        # Get latest quotes from realtime_quotes table
        latest_quotes = {}
        try:
            from sqlalchemy import func
            subquery = db.session.query(
                RealtimeQuote.symbol,
                func.max(RealtimeQuote.timestamp).label('max_timestamp')
            ).group_by(RealtimeQuote.symbol).subquery()

            quotes_query = db.session.query(RealtimeQuote).join(
                subquery,
                db.and_(
                    RealtimeQuote.symbol == subquery.c.symbol,
                    RealtimeQuote.timestamp == subquery.c.max_timestamp
                )
            ).all()

            for quote in quotes_query:
                latest_quotes[quote.symbol] = {
                    'current_price': float(quote.current_price),
                    'change_percent': float(quote.change_percent),
                    'last_update': quote.timestamp
                }

            logger.info(f"✅ Retrieved {len(latest_quotes)} latest quotes from database")
        except Exception as quote_error:
            logger.warning(f"⚠️ Could not fetch latest quotes from database: {quote_error}")
        
        # Process each admin signal
        for signal in signals:
            try:
                # Get current price from latest quotes or use current_price field
                current_price = float(signal.current_price) if signal.current_price else float(signal.entry_price)
                change_percent = float(signal.change_percent) if signal.change_percent else 0

                # Override with latest quote if available
                if signal.symbol in latest_quotes:
                    current_price = latest_quotes[signal.symbol]['current_price']
                    change_percent = latest_quotes[signal.symbol]['change_percent']

                    # Update signal with latest price in database
                    signal.current_price = current_price
                    signal.change_percent = change_percent
                    signal.last_update_time = datetime.utcnow()

                # Calculate values
                entry_price = float(signal.entry_price)
                quantity = signal.quantity
                invested_amount = entry_price * quantity
                current_value = current_price * quantity

                # P&L calculations
                if signal.signal_type.upper() == 'BUY':
                    pnl_amount = (current_price - entry_price) * quantity
                else:  # SELL
                    pnl_amount = (entry_price - current_price) * quantity

                pnl_percent = (pnl_amount / invested_amount * 100) if invested_amount > 0 else 0

                # Target calculations
                target_price = float(signal.target_price) if signal.target_price else 0
                target_value_amount = target_price * quantity if target_price > 0 else 0
                target_profit_return = ((target_price - entry_price) / entry_price) * 100 if target_price > 0 and entry_price > 0 else 0

                # Days held calculation
                days_held = (datetime.utcnow() - signal.created_at).days if signal.created_at else 0

                # Position status
                position_status = 1 if signal.status == 'ACTIVE' else 0

                # Get target user info
                target_user = User.query.get(signal.target_user_id) if signal.target_user_id else None

                # Create signal data matching the expected format
                signal_data = {
                    'id': signal.id,
                    'etf': signal.symbol,
                    'thirty': f"{pnl_percent * 1.2:.1f}%",
                    'dh': str(days_held),
                    'date': signal.created_at.strftime('%d-%b-%Y') if signal.created_at else '',
                    'pos': position_status,
                    'qty': quantity,
                    'ep': entry_price,
                    'cmp': current_price,
                    'change_pct': change_percent,
                    'inv': invested_amount,
                    'tp': target_price,
                    'tva': target_value_amount,
                    'tpr': target_profit_return,
                    'pl': pnl_amount,
                    'ed': signal.expires_at.strftime('%d-%b-%Y') if signal.expires_at else '',
                    'exp': '',
                    'pr': f"{pnl_percent:.1f}%",
                    'pp': '★★★' if signal.priority == 'HIGH' else '★★' if signal.priority == 'MEDIUM' else '★',
                    'iv': invested_amount,
                    'ip': f"{change_percent:.2f}%",
                    'nt': signal.signal_description or f"Trading signal for {signal.symbol}",
                    'qt': datetime.utcnow().strftime('%H:%M'),
                    'seven': f"{pnl_percent * 0.8:.1f}%",
                    'change2': change_percent,
                    'signal_type': signal.signal_type,
                    'status': signal.status,
                    'symbol': signal.symbol,
                    'trading_symbol': signal.trading_symbol,
                    'priority': signal.priority,
                    'target_user_ucc': target_user.ucc if target_user else 'N/A',
                    'target_user_name': target_user.greeting_name if target_user else 'N/A',
                    'invested_amount': invested_amount,
                    'current_value': current_value,
                    'profit_loss': pnl_amount,
                    'profit_loss_percent': pnl_percent,
                    'created_at': signal.created_at.isoformat() if signal.created_at else None,
                    'last_updated': datetime.utcnow().strftime('%H:%M:%S')
                }

                signals_data.append(signal_data)

                # Update totals for portfolio summary
                if signal.status == 'ACTIVE':
                    total_invested += invested_amount
                    total_current_value += current_value
                    total_pnl += pnl_amount

            except Exception as signal_error:
                logger.error(f"Error processing signal {signal.id}: {signal_error}")
                continue

        # Commit price updates to database
        if latest_quotes:
            try:
                db.session.commit()
                logger.info("✅ Updated signal prices in database")
            except Exception as commit_error:
                logger.warning(f"⚠️ Could not update prices: {commit_error}")
                db.session.rollback()

        # Calculate portfolio summary
        active_signals = len([s for s in signals_data if s.get('status') == 'ACTIVE'])
        profit_signals = len([s for s in signals_data if s.get('profit_loss', 0) > 0])
        loss_signals = len([s for s in signals_data if s.get('profit_loss', 0) < 0])

        portfolio_summary = {
            'total_trades': len(signals_data),
            'active_trades': active_signals,
            'profit_trades': profit_signals,
            'loss_trades': loss_signals,
            'total_invested': total_invested,
            'total_investment': total_invested,
            'total_current_value': total_current_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            'total_positions': len(signals_data),
            'current_value': total_current_value,
            'return_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            'active_positions': active_signals,
            'closed_positions': len([s for s in signals_data if s.get('status') != 'ACTIVE'])
        }

        return jsonify({
            'success': True,
            'signals': signals_data,
            'total': len(signals_data),
            'portfolio': portfolio_summary,
            'last_update': datetime.utcnow().isoformat(),
            'quotes_fetched': len(latest_quotes)
        })

    except Exception as e:
        logger.error(f"Error fetching ETF signals data: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch signals data',
            'success': False,
            'signals': [],
            'total': 0,
            'portfolio': {
                'total_positions': 0,
                'total_investment': 0,
                'current_value': 0,
                'total_pnl': 0,
                'return_percent': 0,
                'active_positions': 0,
                'closed_positions': 0
            }
        }), 500