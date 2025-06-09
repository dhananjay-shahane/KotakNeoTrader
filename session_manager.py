
import os
import json
import logging
from datetime import datetime, timedelta

class SessionManager:
    """Manages persistent session storage for Kotak Neo tokens"""
    
    def __init__(self, storage_file='user_sessions.json'):
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        self.sessions = self.load_sessions()
    
    def load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading sessions: {e}")
            return {}
    
    def save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving sessions: {e}")
    
    def store_session(self, user_id, session_data):
        """Store session data for a user"""
        try:
            self.sessions[user_id] = {
                'access_token': session_data.get('access_token'),
                'session_token': session_data.get('session_token'),
                'sid': session_data.get('sid'),
                'ucc': session_data.get('ucc'),
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(hours=24),
                'authenticated': True
            }
            self.save_sessions()
            self.logger.info(f"Session stored for user: {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error storing session: {e}")
            return False
    
    def get_session(self, user_id):
        """Get session data for a user"""
        try:
            if user_id in self.sessions:
                session_data = self.sessions[user_id]
                # Check if session is still valid
                if datetime.fromisoformat(str(session_data['expires_at'])) > datetime.now():
                    return session_data
                else:
                    self.remove_session(user_id)
                    self.logger.info(f"Session expired for user: {user_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting session: {e}")
            return None
    
    def remove_session(self, user_id):
        """Remove session for a user"""
        try:
            if user_id in self.sessions:
                del self.sessions[user_id]
                self.save_sessions()
                self.logger.info(f"Session removed for user: {user_id}")
        except Exception as e:
            self.logger.error(f"Error removing session: {e}")
    
    def get_valid_session(self):
        """Get any valid session (for apps with single user)"""
        try:
            for user_id, session_data in self.sessions.items():
                if datetime.fromisoformat(str(session_data['expires_at'])) > datetime.now():
                    return session_data
            return None
        except Exception as e:
            self.logger.error(f"Error getting valid session: {e}")
            return None
    
    def clean_expired_sessions(self):
        """Remove all expired sessions"""
        try:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, session_data in self.sessions.items():
                if datetime.fromisoformat(str(session_data['expires_at'])) <= current_time:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.sessions[user_id]
            
            if expired_users:
                self.save_sessions()
                self.logger.info(f"Cleaned {len(expired_users)} expired sessions")
        except Exception as e:
            self.logger.error(f"Error cleaning expired sessions: {e}")
