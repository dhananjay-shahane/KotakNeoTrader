from app import db
from models_etf import ETFPosition, ETFWatchlist
from neo_client import NeoClient
from session_helper import SessionHelper
from datetime import datetime, timedelta
import logging
import json
import pandas as pd

logger = logging.getLogger(__name__)


class ETFTradingSignals:
    """ETF Trading Signals Manager with real-time data integration"""
    
    def __init__(self):
        self.session_helper = SessionHelper()
        self.neo_client = NeoClient()
        self.client = None
        self.websocket_subscriptions = set()
        
    def initialize_client(self):
        """Initialize Neo API client with stored session"""
        try:
            user_data = self.session_helper.get_current_user_data()
            if not user_data:
                logger.error("No user session data found")
                return False
                
            access_token = user_data.get('access_token')
            session_token = user_data.get('session_token')
            sid = user_data.get('sid')
            
            if not all([access_token, session_token, sid]):
                logger.error("Missing required tokens for Neo client")
                return False
                
            self.client = self.neo_client.initialize_client_with_tokens(
                access_token, session_token, sid
            )
            
            if self.client:
                logger.info("✅ Neo client initialized successfully")
                return True
            else:
                logger.error("Failed to initialize Neo client")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Neo client: {e}")
            return False
    
    def search_etf_instruments(self, query):
        """Search for ETF instruments using Neo API"""
        if not self.client:
            if not self.initialize_client():
                return []
        
        try:
            # Search for instruments with the query
            search_results = self.client.search_scrip(exchange_segment="nse_cm", symbol=query)
            
            etf_results = []
            if isinstance(search_results, list):
                for instrument in search_results:
                    # Filter for ETFs only
                    if (isinstance(instrument, dict) and 
                        ('ETF' in instrument.get('pSymbol', '').upper() or 
                         'ETF' in instrument.get('pDesc', '').upper() or
                         instrument.get('pSymbol', '').endswith('ETF'))):
                        
                        etf_results.append({
                            'symbol': instrument.get('pSymbol', ''),
                            'trading_symbol': instrument.get('pTrdSymbol', ''),
                            'token': str(instrument.get('pSymbolName', '')),
                            'exchange': instrument.get('pExchSeg', 'nse_cm'),
                            'description': instrument.get('pDesc', ''),
                            'lot_size': instrument.get('pLotSize', 1)
                        })
            
            logger.info(f"Found {len(etf_results)} ETF instruments for query: {query}")
            return etf_results
            
        except Exception as e:
            logger.error(f"Error searching ETF instruments: {e}")
            return []
    
    def get_live_quotes(self, instruments):
        """Get live quotes for multiple instruments"""
        if not self.client:
            if not self.initialize_client():
                return {}
        
        try:
            quotes = {}
            for instrument in instruments:
                try:
                    quote_data = self.client.quote(
                        instrument_token=instrument['token'],
                        exchange_segment=instrument['exchange']
                    )
                    
                    if quote_data and isinstance(quote_data, dict):
                        quotes[instrument['token']] = {
                            'ltp': quote_data.get('ltp', 0),
                            'change': quote_data.get('nc', 0),
                            'change_percent': quote_data.get('pc', 0),
                            'volume': quote_data.get('volume', 0),
                            'high': quote_data.get('h', 0),
                            'low': quote_data.get('l', 0),
                            'open': quote_data.get('o', 0),
                            'close': quote_data.get('c', 0)
                        }
                except Exception as e:
                    logger.error(f"Error getting quote for {instrument['symbol']}: {e}")
                    continue
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting live quotes: {e}")
            return {}
    
    def add_etf_position(self, user_id, position_data):
        """Add new ETF position"""
        try:
            # Validate required fields
            required_fields = ['etf_symbol', 'trading_symbol', 'token', 'quantity', 'entry_price']
            for field in required_fields:
                if field not in position_data or not position_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create new position
            position = ETFPosition(
                user_id=user_id,
                etf_symbol=position_data['etf_symbol'],
                trading_symbol=position_data['trading_symbol'],
                token=position_data['token'],
                exchange=position_data.get('exchange', 'NSE'),
                entry_date=datetime.strptime(position_data.get('entry_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                quantity=int(position_data['quantity']),
                entry_price=float(position_data['entry_price']),
                target_price=float(position_data['target_price']) if position_data.get('target_price') else None,
                stop_loss=float(position_data['stop_loss']) if position_data.get('stop_loss') else None,
                position_type=position_data.get('position_type', 'LONG'),
                notes=position_data.get('notes', '')
            )
            
            db.session.add(position)
            db.session.commit()
            
            # Subscribe to live data for this instrument
            self.subscribe_to_live_data([{
                'token': position.token,
                'exchange': position.exchange,
                'symbol': position.etf_symbol
            }])
            
            logger.info(f"✅ Added ETF position: {position.etf_symbol}")
            return position.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding ETF position: {e}")
            raise
    
    def update_etf_position(self, position_id, user_id, update_data):
        """Update existing ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")
            
            # Update allowed fields
            updatable_fields = ['quantity', 'entry_price', 'target_price', 'stop_loss', 'notes', 'position_type']
            for field in updatable_fields:
                if field in update_data:
                    if field in ['quantity', 'entry_price', 'target_price', 'stop_loss']:
                        setattr(position, field, float(update_data[field]) if update_data[field] else None)
                    else:
                        setattr(position, field, update_data[field])
            
            position.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Updated ETF position: {position.etf_symbol}")
            return position.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ETF position: {e}")
            raise
    
    def delete_etf_position(self, position_id, user_id):
        """Delete ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")
            
            # Unsubscribe from live data
            self.unsubscribe_from_live_data([{
                'token': position.token,
                'exchange': position.exchange
            }])
            
            db.session.delete(position)
            db.session.commit()
            
            logger.info(f"✅ Deleted ETF position: {position.etf_symbol}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting ETF position: {e}")
            raise
    
    def get_user_etf_positions(self, user_id):
        """Get all ETF positions for a user"""
        try:
            positions = ETFPosition.query.filter_by(user_id=user_id, is_active=True).all()
            
            # Get live quotes for all positions
            instruments = [{'token': p.token, 'exchange': p.exchange, 'symbol': p.etf_symbol} for p in positions]
            live_quotes = self.get_live_quotes(instruments)
            
            # Update positions with live data
            position_data = []
            for position in positions:
                pos_dict = position.to_dict()
                
                # Update with live quote if available
                if position.token in live_quotes:
                    quote = live_quotes[position.token]
                    position.current_price = quote['ltp']
                    position.last_update_time = datetime.utcnow()
                    
                    # Recalculate metrics with live data
                    pos_dict.update({
                        'current_price': quote['ltp'],
                        'profit_loss': position.profit_loss,
                        'percentage_change': position.percentage_change,
                        'current_value': position.current_value,
                        'last_update_time': datetime.utcnow().isoformat(),
                        'live_data': quote
                    })
                
                position_data.append(pos_dict)
            
            # Commit live price updates
            db.session.commit()
            
            return position_data
            
        except Exception as e:
            logger.error(f"Error getting user ETF positions: {e}")
            return []
    
    def subscribe_to_live_data(self, instruments):
        """Subscribe to live data using WebSocket"""
        if not self.client:
            if not self.initialize_client():
                return False
        
        try:
            # Prepare instrument tokens for subscription
            tokens_to_subscribe = []
            for instrument in instruments:
                token = instrument['token']
                if token not in self.websocket_subscriptions:
                    tokens_to_subscribe.append(token)
                    self.websocket_subscriptions.add(token)
            
            if tokens_to_subscribe:
                # Subscribe to live data feed
                subscription_result = self.client.subscribe_to_orderfeed()
                logger.info(f"Subscribed to live data for {len(tokens_to_subscribe)} instruments")
                
                # Setup WebSocket callbacks for price updates
                self.setup_websocket_callbacks()
                
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to live data: {e}")
            return False
    
    def unsubscribe_from_live_data(self, instruments):
        """Unsubscribe from live data"""
        try:
            for instrument in instruments:
                token = instrument['token']
                if token in self.websocket_subscriptions:
                    self.websocket_subscriptions.remove(token)
            
            logger.info(f"Unsubscribed from live data for {len(instruments)} instruments")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from live data: {e}")
            return False
    
    def setup_websocket_callbacks(self):
        """Setup WebSocket callbacks for live price updates"""
        def on_message(message):
            """Handle incoming WebSocket messages"""
            try:
                if isinstance(message, dict):
                    token = message.get('tk')
                    ltp = message.get('ltp')
                    
                    if token and ltp:
                        # Update positions with new price data
                        self.update_positions_with_live_data(token, {
                            'ltp': ltp,
                            'change': message.get('nc', 0),
                            'change_percent': message.get('pc', 0),
                            'volume': message.get('v', 0)
                        })
                        
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
        
        def on_error(error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(message):
            logger.info("WebSocket connection closed")
        
        # Set callbacks if client supports it
        if hasattr(self.client, 'set_on_message'):
            self.client.set_on_message(on_message)
            self.client.set_on_error(on_error)
            self.client.set_on_close(on_close)
    
    def update_positions_with_live_data(self, token, quote_data):
        """Update ETF positions with live market data"""
        try:
            positions = ETFPosition.query.filter_by(token=str(token), is_active=True).all()
            
            for position in positions:
                position.current_price = quote_data['ltp']
                position.last_update_time = datetime.utcnow()
            
            db.session.commit()
            logger.debug(f"Updated {len(positions)} positions with live data for token {token}")
            
        except Exception as e:
            logger.error(f"Error updating positions with live data: {e}")
    
    def calculate_portfolio_summary(self, user_id):
        """Calculate portfolio summary metrics"""
        try:
            positions = ETFPosition.query.filter_by(user_id=user_id, is_active=True).all()
            
            total_investment = sum(p.investment_amount for p in positions)
            total_current_value = sum(p.current_value for p in positions)
            total_pnl = sum(p.profit_loss for p in positions)
            
            portfolio_return_pct = 0
            if total_investment > 0:
                portfolio_return_pct = (total_pnl / total_investment) * 100
            
            return {
                'total_positions': len(positions),
                'total_investment': total_investment,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'portfolio_return_percent': portfolio_return_pct,
                'profitable_positions': len([p for p in positions if p.profit_loss > 0]),
                'loss_positions': len([p for p in positions if p.profit_loss < 0])
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio summary: {e}")
            return {}