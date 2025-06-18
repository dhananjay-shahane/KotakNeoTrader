from app import app, db
from models import User
from models_etf import ETFPosition, ETFWatchlist
from api.etf_signals import get_etf_positions
import logging

# Register ETF API endpoints
app.add_url_rule('/api/etf_positions', 'get_etf_positions', get_etf_positions, methods=['GET'])