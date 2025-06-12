"""Admin API endpoints"""
from flask import Blueprint, jsonify, session
from sqlalchemy import text
import logging

from utils.auth import login_required
from models import db, User, UserSession, UserPreferences
from user_manager import UserManager

admin_api = Blueprint('admin_api', __name__, url_prefix='/api')

# Initialize components
user_manager = UserManager()

@admin_api.route('/users')
@login_required
def get_users():
    """Get all users from database"""
    try:
        users = User.query.filter_by(is_active=True).all()
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            "success": True,
            "data": users_data,
            "count": len(users_data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_api.route('/user/<int:user_id>')
@login_required
def get_user(user_id):
    """Get specific user by ID"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get user sessions
        sessions = UserSession.query.filter_by(user_id=user_id).order_by(UserSession.created_at.desc()).limit(5).all()
        sessions_data = []
        for s in sessions:
            sessions_data.append({
                "id": s.id,
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "is_active": s.is_active
            })
        
        return jsonify({
            "success": True,
            "data": {
                "user": user.to_dict(),
                "recent_sessions": sessions_data
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_api.route('/user-stats')
@login_required
def get_user_stats():
    """Get user statistics"""
    try:
        stats = user_manager.get_user_stats()
        
        # Get additional stats
        total_sessions = UserSession.query.count()
        from datetime import datetime, timedelta
        recent_logins = User.query.filter(
            User.last_login > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        stats.update({
            "total_sessions": total_sessions,
            "recent_logins_24h": recent_logins
        })
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_api.route('/current-user')
@login_required
def get_current_user():
    """Get current logged-in user data"""
    try:
        db_user_id = session.get('db_user_id')
        if db_user_id:
            user = User.query.get(db_user_id)
            if user:
                return jsonify({
                    "success": True,
                    "data": user.to_dict()
                })
        
        # Fallback to session data
        return jsonify({
            "success": True,
            "data": {
                "ucc": session.get('ucc'),
                "greeting_name": session.get('greeting_name'),
                "login_time": session.get('login_time'),
                "is_trial_account": session.get('is_trial_account', False)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_api.route('/database-status')
@login_required
def database_status():
    """Check database connection and show stored data"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        # Get counts
        user_count = User.query.count()
        session_count = UserSession.query.count()
        preference_count = UserPreferences.query.count()
        
        # Get sample data if exists
        sample_user = User.query.first()
        sample_data = None
        if sample_user:
            sample_data = {
                "ucc": sample_user.ucc,
                "sid": sample_user.sid,
                "rid": sample_user.rid,
                "greeting_name": sample_user.greeting_name,
                "last_login": sample_user.last_login.isoformat() if sample_user.last_login else None
            }
        
        return jsonify({
            "success": True,
            "database_connected": True,
            "tables": {
                "users": user_count,
                "user_sessions": session_count,
                "user_preferences": preference_count
            },
            "sample_user_data": sample_data,
            "data_fields_stored": [
                "ucc", "mobile_number", "greeting_name", "user_id", 
                "client_code", "product_code", "account_type", "branch_code",
                "is_trial_account", "access_token", "session_token", 
                "sid", "rid", "created_at", "updated_at", "last_login",
                "session_expires_at", "is_active"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "database_connected": False,
            "error": str(e)
        }), 500