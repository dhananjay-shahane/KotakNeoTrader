from app import app, db
from models import User
from models_etf import ETFPosition, ETFWatchlist
import logging

# Register additional blueprints
try:
    from api.admin import admin_bp
    app.register_blueprint(admin_bp)
except ImportError as e:
    logging.warning(f"Could not import admin blueprint: {e}")

try:
    from api.deals import deals_bp
    app.register_blueprint(deals_bp)
except ImportError as e:
    logging.warning(f"Could not import deals blueprint: {e}")

try:
    from api.etf_signals import etf_bp
    app.register_blueprint(etf_bp)
except ImportError as e:
    logging.warning(f"Could not import ETF signals blueprint: {e}")