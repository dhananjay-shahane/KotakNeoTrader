
from app import app, db
from models import User
from models_etf import ETFPosition, ETFWatchlist
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Import blueprints only once
try:
    from routes.main import main_bp
    from routes.auth import auth_bp
    from api.trading import trading_api
    from api.dashboard import dashboard_api
    from api.admin import admin_api
    from api.etf_signals import etf_signals_api, get_etf_positions
except ImportError as e:
    logging.error(f"Import error: {e}")
    # Create minimal blueprints if imports fail
    from flask import Blueprint
    main_bp = Blueprint('main_fallback', __name__)
    auth_bp = Blueprint('auth_fallback', __name__)

# Register blueprints only if not already registered
def register_blueprint_safe(app, blueprint, **options):
    """Safely register blueprint if not already registered"""
    blueprint_name = options.get('name', blueprint.name)
    if blueprint_name not in app.blueprints:
        app.register_blueprint(blueprint, **options)
        logging.info(f"Registered blueprint: {blueprint_name}")
    else:
        logging.warning(f"Blueprint {blueprint_name} already registered, skipping")

# Register all blueprints safely
try:
    register_blueprint_safe(app, main_bp)
    register_blueprint_safe(app, auth_bp)
    register_blueprint_safe(app, trading_api, url_prefix='/api')
    register_blueprint_safe(app, dashboard_api, url_prefix='/api')
    register_blueprint_safe(app, admin_api, url_prefix='/api/admin')
    register_blueprint_safe(app, etf_signals_api, url_prefix='/api')
except Exception as e:
    logging.error(f"Blueprint registration error: {e}")

# Register ETF API endpoints
try:
    app.add_url_rule('/api/etf_positions', 'get_etf_positions', get_etf_positions, methods=['GET'])
except Exception as e:
    logging.error(f"URL rule registration error: {e}")

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Database creation error: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
