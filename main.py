from app import app, db
from models import User
from models_etf import ETFPosition, ETFWatchlist
from api.etf_signals import get_etf_positions, get_user_etf_signal_trades, update_etf_signal_trade
import logging
from api.admin import admin_bp
from api.deals import deals_bp

# Register ETF API endpoints
app.add_url_rule('/api/etf_positions', 'get_etf_positions', get_etf_positions, methods=['GET'])
app.add_url_rule('/api/etf_signal_trades', 'get_user_etf_signal_trades', get_user_etf_signal_trades, methods=['GET'])
app.add_url_rule('/api/etf_signal_trades/update', 'update_etf_signal_trade', update_etf_signal_trade, methods=['PUT'])
app.register_blueprint(admin_bp)
app.register_blueprint(deals_bp)