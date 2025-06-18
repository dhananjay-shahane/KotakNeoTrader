from app import app, db
from models import User
from models_etf import ETFPosition, ETFWatchlist
from api.etf_signals import get_etf_positions
import logging

# Register ETF API endpoints
app.add_url_rule('/api/etf_positions', 'get_etf_positions', get_etf_positions, methods=['GET'])
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(trading_api, url_prefix='/api')
app.register_blueprint(dashboard_api, url_prefix='/api')
app.register_blueprint(admin_api, url_prefix='/api/admin')

# Import and register ETF signals API
from api.etf_signals import etf_signals_api
app.register_blueprint(etf_signals_api, url_prefix='/api')