"""
Real-time Quotes Manager for ETF Trading Signals
Fetches and stores CMP data every 5 minutes using Kotak Neo API
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
import schedule
from app import db, app
from models_etf import RealtimeQuote, ETFSignalTrade, AdminTradeSignal
from trading_functions import TradingFunctions
import json

logger = logging.getLogger(__name__)

class RealtimeQuotesManager:
    """Manages real-time quotes fetching and storage"""
    
    def __init__(self):
        self.trading_functions = None
        self.scheduler_thread = None
        self.is_running = False
        self.etf_symbols = [
            'NIFTYBEES', 'BANKBEES', 'GOLDSHARE', 'ITBEES', 'PSUBNKBEES',
            'JUNIORBEES', 'LIQUIDBEES', 'CPSE ETF', 'KOTAKPSU', 'ICICIB22',
            'HDFCNIFTY', 'KOTAKNV20', 'ICICINXT50', 'RELGOLD', 'AXISGOLD',
            'HDFCGOLD', 'ICICIPRUH', 'KOTAKSILV', 'ICICINIFTY', 'AXISBNK'
        ]
        
    def initialize_trading_functions(self):
        """Initialize trading functions with current session"""
        try:
            self.trading_functions = TradingFunctions()
            if hasattr(self.trading_functions, 'initialize_neo_client'):
                self.trading_functions.initialize_neo_client()
            logger.info("Trading functions initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize trading functions: {str(e)}")
            return False
    
    def get_unique_symbols_from_signals(self):
        """Get unique symbols from all active signals"""
        try:
            with app.app_context():
                # Get symbols from ETF signal trades
                etf_symbols = db.session.query(ETFSignalTrade.symbol).filter(
                    ETFSignalTrade.status == 'ACTIVE'
                ).distinct().all()
                
                # Get symbols from admin trade signals
                admin_symbols = db.session.query(AdminTradeSignal.symbol).filter(
                    AdminTradeSignal.status == 'ACTIVE'
                ).distinct().all()
                
                # Combine and deduplicate
                all_symbols = set()
                for symbol in etf_symbols:
                    all_symbols.add(symbol[0])
                for symbol in admin_symbols:
                    all_symbols.add(symbol[0])
                
                # Add default ETF symbols
                all_symbols.update(self.etf_symbols)
                
                return list(all_symbols)
        except Exception as e:
            logger.error(f"Error getting symbols from signals: {str(e)}")
            return self.etf_symbols
    
    def fetch_quote_for_symbol(self, symbol):
        """Fetch real-time quote for a single symbol"""
        try:
            if not self.trading_functions:
                return None
                
            # Search for the instrument
            search_results = self.trading_functions.search_instruments(symbol)
            if not search_results or len(search_results) == 0:
                logger.warning(f"No instrument found for symbol: {symbol}")
                return None
            
            # Use the first match
            instrument = search_results[0]
            token = instrument.get('tk', '')
            
            # Get quote data
            quote_data = self.trading_functions.get_quotes([token])
            if not quote_data or len(quote_data) == 0:
                logger.warning(f"No quote data for symbol: {symbol}")
                return None
            
            quote = quote_data[0]
            
            # Parse the quote data
            current_price = float(quote.get('ltp', 0))
            open_price = float(quote.get('o', 0))
            high_price = float(quote.get('h', 0))
            low_price = float(quote.get('l', 0))
            close_price = float(quote.get('c', 0))
            
            # Calculate change
            change_amount = current_price - close_price if close_price > 0 else 0
            change_percent = (change_amount / close_price * 100) if close_price > 0 else 0
            
            return {
                'symbol': symbol,
                'trading_symbol': instrument.get('ts', f"{symbol}-EQ"),
                'token': token,
                'exchange': instrument.get('e', 'NSE'),
                'current_price': current_price,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'change_amount': change_amount,
                'change_percent': change_percent,
                'volume': int(quote.get('v', 0)),
                'avg_volume': int(quote.get('av', 0)),
                'market_status': 'OPEN' if quote.get('stat', '') == 'Ok' else 'CLOSED'
            }
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None
    
    def store_quote(self, quote_data):
        """Store quote data in database"""
        try:
            with app.app_context():
                realtime_quote = RealtimeQuote(
                    symbol=quote_data['symbol'],
                    trading_symbol=quote_data['trading_symbol'],
                    token=quote_data['token'],
                    exchange=quote_data['exchange'],
                    current_price=Decimal(str(quote_data['current_price'])),
                    open_price=Decimal(str(quote_data['open_price'])),
                    high_price=Decimal(str(quote_data['high_price'])),
                    low_price=Decimal(str(quote_data['low_price'])),
                    close_price=Decimal(str(quote_data['close_price'])),
                    change_amount=Decimal(str(quote_data['change_amount'])),
                    change_percent=Decimal(str(quote_data['change_percent'])),
                    volume=quote_data['volume'],
                    avg_volume=quote_data['avg_volume'],
                    timestamp=datetime.utcnow(),
                    market_status=quote_data['market_status'],
                    data_source='KOTAK_NEO',
                    fetch_status='SUCCESS'
                )
                
                db.session.add(realtime_quote)
                db.session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing quote for {quote_data['symbol']}: {str(e)}")
            db.session.rollback()
            return False
    
    def update_signal_prices(self, symbol, current_price):
        """Update current prices in signal tables"""
        try:
            with app.app_context():
                # Update ETF signal trades
                etf_trades = ETFSignalTrade.query.filter(
                    ETFSignalTrade.symbol == symbol,
                    ETFSignalTrade.status == 'ACTIVE'
                ).all()
                
                for trade in etf_trades:
                    trade.current_price = Decimal(str(current_price))
                    trade.last_price_update = datetime.utcnow()
                    trade.calculate_pnl()
                
                # Update admin trade signals
                admin_signals = AdminTradeSignal.query.filter(
                    AdminTradeSignal.symbol == symbol,
                    AdminTradeSignal.status == 'ACTIVE'
                ).all()
                
                for signal in admin_signals:
                    old_price = float(signal.current_price) if signal.current_price else 0
                    signal.current_price = Decimal(str(current_price))
                    signal.last_update_time = datetime.utcnow()
                    
                    # Calculate change percent
                    if old_price > 0:
                        change_pct = ((current_price - old_price) / old_price) * 100
                        signal.change_percent = Decimal(str(change_pct))
                
                db.session.commit()
                logger.debug(f"Updated prices for {len(etf_trades)} ETF trades and {len(admin_signals)} admin signals")
                
        except Exception as e:
            logger.error(f"Error updating signal prices for {symbol}: {str(e)}")
            db.session.rollback()
    
    def fetch_all_quotes(self):
        """Fetch quotes for all symbols and store them"""
        try:
            if not self.initialize_trading_functions():
                logger.error("Cannot fetch quotes - trading functions not initialized")
                return False
            
            symbols = self.get_unique_symbols_from_signals()
            logger.info(f"Fetching quotes for {len(symbols)} symbols: {symbols}")
            
            successful_fetches = 0
            failed_fetches = 0
            
            for symbol in symbols:
                try:
                    quote_data = self.fetch_quote_for_symbol(symbol)
                    if quote_data:
                        # Store in realtime_quotes table
                        if self.store_quote(quote_data):
                            # Update prices in signal tables
                            self.update_signal_prices(symbol, quote_data['current_price'])
                            successful_fetches += 1
                            logger.debug(f"Successfully processed quote for {symbol}: ₹{quote_data['current_price']}")
                        else:
                            failed_fetches += 1
                    else:
                        failed_fetches += 1
                        
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol}: {str(e)}")
                    failed_fetches += 1
                    continue
            
            logger.info(f"Quote fetch completed: {successful_fetches} successful, {failed_fetches} failed")
            return successful_fetches > 0
            
        except Exception as e:
            logger.error(f"Error in fetch_all_quotes: {str(e)}")
            return False
    
    def cleanup_old_quotes(self, days_to_keep=7):
        """Clean up old quote data to prevent database bloat"""
        try:
            with app.app_context():
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                deleted_count = RealtimeQuote.query.filter(
                    RealtimeQuote.timestamp < cutoff_date
                ).delete()
                db.session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old quote records")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old quotes: {str(e)}")
            db.session.rollback()
    
    def get_latest_quotes(self, symbols=None):
        """Get latest quotes for specified symbols or all symbols"""
        try:
            with app.app_context():
                query = db.session.query(RealtimeQuote)
                
                if symbols:
                    query = query.filter(RealtimeQuote.symbol.in_(symbols))
                
                # Get the latest quote for each symbol
                subquery = db.session.query(
                    RealtimeQuote.symbol,
                    db.func.max(RealtimeQuote.timestamp).label('max_timestamp')
                ).group_by(RealtimeQuote.symbol).subquery()
                
                latest_quotes = db.session.query(RealtimeQuote).join(
                    subquery,
                    db.and_(
                        RealtimeQuote.symbol == subquery.c.symbol,
                        RealtimeQuote.timestamp == subquery.c.max_timestamp
                    )
                ).all()
                
                return [quote.to_dict() for quote in latest_quotes]
                
        except Exception as e:
            logger.error(f"Error getting latest quotes: {str(e)}")
            return []
    
    def start_scheduler(self):
        """Start the quote fetching scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting realtime quotes scheduler...")
        
        # Schedule quote fetching every 5 minutes
        schedule.every(5).minutes.do(self.fetch_all_quotes)
        
        # Schedule cleanup daily at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_old_quotes)
        
        # Run initial fetch
        self.fetch_all_quotes()
        
        def run_scheduler():
            self.is_running = True
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {str(e)}")
                    time.sleep(60)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Realtime quotes scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the quote fetching scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping realtime quotes scheduler...")
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Realtime quotes scheduler stopped")

# Global instance
realtime_quotes_manager = RealtimeQuotesManager()

def start_quotes_scheduler():
    """Start the global quotes scheduler"""
    realtime_quotes_manager.start_scheduler()

def stop_quotes_scheduler():
    """Stop the global quotes scheduler"""
    realtime_quotes_manager.stop_scheduler()

def get_latest_quotes_api(symbols=None):
    """API function to get latest quotes"""
    return realtime_quotes_manager.get_latest_quotes(symbols)

def force_fetch_quotes():
    """Force an immediate quote fetch"""
    return realtime_quotes_manager.fetch_all_quotes()