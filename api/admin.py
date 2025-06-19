"""
Admin API endpoints for trade signal management
"""
from flask import Blueprint, request, jsonify, session
from models import db, User
from models_etf import AdminTradeSignal, UserNotification
from datetime import datetime, timedelta
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/send-signal', methods=['POST'])
def send_trade_signal():
    """Send trade signal to specific user"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Get admin user
        admin_user = User.query.get(session['user_id'])
        if not admin_user:
            return jsonify({'success': False, 'message': 'Admin user not found'}), 404
        
        # For now, allow all users to send signals (you can add admin role check here)
        # if not admin_user.is_admin:  # Add this field to User model if needed
        #     return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['target_user_id', 'symbol', 'signal_type', 'entry_price', 'quantity', 'signal_title']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if target user exists
        target_user = User.query.get(data['target_user_id'])
        if not target_user:
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Create trade signal
        signal = AdminTradeSignal(
            admin_user_id=admin_user.id,
            target_user_id=data['target_user_id'],
            symbol=data['symbol'].upper(),
            trading_symbol=data['symbol'].upper(),  # Simplified for now
            token=f"TOKEN_{data['symbol'].upper()}",  # Simplified for now
            exchange=data.get('exchange', 'NSE'),
            signal_type=data['signal_type'].upper(),
            entry_price=float(data['entry_price']),
            target_price=float(data['target_price']) if data.get('target_price') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            quantity=int(data['quantity']),
            signal_title=data['signal_title'],
            signal_description=data.get('signal_description'),
            priority=data.get('priority', 'MEDIUM').upper(),
            expires_at=datetime.utcnow() + timedelta(days=7)  # Signal expires in 7 days
        )
        
        db.session.add(signal)
        db.session.flush()  # Get the signal ID
        
        # Create notification for target user
        notification = UserNotification(
            user_id=data['target_user_id'],
            title=f"New Trade Signal: {data['signal_title']}",
            message=f"{data['signal_type']} {data['symbol']} @ ₹{data['entry_price']} - {data.get('signal_description', 'No description')}",
            notification_type='TRADE_SIGNAL',
            priority=data.get('priority', 'MEDIUM').upper(),
            related_signal_id=signal.id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"Trade signal sent from user {admin_user.id} to user {data['target_user_id']}: {data['signal_title']}")
        
        return jsonify({
            'success': True,
            'message': 'Trade signal sent successfully',
            'signal_id': signal.id
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending trade signal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending signal: {str(e)}'}), 500

@admin_bp.route('/signals', methods=['GET'])
def get_sent_signals():
    """Get all signals sent by current admin"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        signals = AdminTradeSignal.query.filter_by(admin_user_id=session['user_id']).order_by(AdminTradeSignal.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'signals': [signal.to_dict() for signal in signals]
        })
        
    except Exception as e:
        logging.error(f"Error fetching sent signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching signals: {str(e)}'}), 500

@admin_bp.route('/users', methods=['GET'])
def get_users_list():
    """Get list of users for admin to send signals to"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        users = User.query.filter(User.id != session['user_id']).all()
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'ucc': user.ucc,
                'greeting_name': user.greeting_name,
                'mobile_number': user.mobile_number
            } for user in users]
        })
        
    except Exception as e:
        logging.error(f"Error fetching users list: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching users: {str(e)}'}), 500