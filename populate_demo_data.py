"""
Populate demo data for trading signals management system
Creates sample ETF signals, realtime quotes, and test data
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from models_etf import ETFSignalTrade, AdminTradeSignal, RealtimeQuote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_users():
    """Create demo users for testing"""
    users_data = [
        {
            'ucc': 'ADMIN001',
            'mobile_number': '9999999999',
            'greeting_name': 'Admin User',
            'user_id': 'admin001',
            'is_active': True
        },
        {
            'ucc': 'USER001',
            'mobile_number': '9876543210',
            'greeting_name': 'John Doe',
            'user_id': 'user001',
            'is_active': True
        },
        {
            'ucc': 'USER002',
            'mobile_number': '9876543211',
            'greeting_name': 'Jane Smith',
            'user_id': 'user002',
            'is_active': True
        },
        {
            'ucc': 'USER003',
            'mobile_number': '9876543212',
            'greeting_name': 'Robert Wilson',
            'user_id': 'user003',
            'is_active': True
        },
        {
            'ucc': 'USER004',
            'mobile_number': '9876543213',
            'greeting_name': 'Sarah Johnson',
            'user_id': 'user004',
            'is_active': True
        }
    ]
    
    created_users = []
    for user_data in users_data:
        existing_user = User.query.filter_by(ucc=user_data['ucc']).first()
        if not existing_user:
            user = User(**user_data)
            db.session.add(user)
            created_users.append(user)
            logger.info(f"Created user: {user_data['greeting_name']} ({user_data['ucc']})")
        else:
            created_users.append(existing_user)
            logger.info(f"User already exists: {user_data['greeting_name']} ({user_data['ucc']})")
    
    db.session.commit()
    return created_users

def create_sample_quotes():
    """Create sample realtime quotes for ETF symbols"""
    etf_symbols = [
        {'symbol': 'NIFTYBEES', 'base_price': 245.50},
        {'symbol': 'BANKBEES', 'base_price': 520.75},
        {'symbol': 'GOLDSHARE', 'base_price': 4850.00},
        {'symbol': 'ITBEES', 'base_price': 385.25},
        {'symbol': 'PSUBNKBEES', 'base_price': 15.80},
        {'symbol': 'JUNIORBEES', 'base_price': 680.40},
        {'symbol': 'LIQUIDBEES', 'base_price': 1000.00},
        {'symbol': 'CPSE ETF', 'base_price': 35.60},
        {'symbol': 'KOTAKPSU', 'base_price': 42.30},
        {'symbol': 'ICICIB22', 'base_price': 78.90}
    ]
    
    created_quotes = 0
    for etf in etf_symbols:
        # Create multiple quote entries with time progression
        for i in range(5):  # 5 quotes per symbol
            timestamp = datetime.utcnow() - timedelta(minutes=i*5)
            
            # Generate realistic price movement
            price_change = random.uniform(-0.02, 0.02)  # ±2% change
            current_price = etf['base_price'] * (1 + price_change)
            
            # Calculate other prices
            open_price = current_price * random.uniform(0.995, 1.005)
            high_price = max(current_price, open_price) * random.uniform(1.0, 1.01)
            low_price = min(current_price, open_price) * random.uniform(0.99, 1.0)
            close_price = etf['base_price']  # Previous day close
            
            change_amount = current_price - close_price
            change_percent = (change_amount / close_price) * 100
            
            quote = RealtimeQuote(
                symbol=etf['symbol'],
                trading_symbol=f"{etf['symbol']}-EQ",
                token=f"TK{random.randint(10000, 99999)}",
                exchange='NSE',
                current_price=Decimal(str(round(current_price, 2))),
                open_price=Decimal(str(round(open_price, 2))),
                high_price=Decimal(str(round(high_price, 2))),
                low_price=Decimal(str(round(low_price, 2))),
                close_price=Decimal(str(round(close_price, 2))),
                change_amount=Decimal(str(round(change_amount, 2))),
                change_percent=Decimal(str(round(change_percent, 2))),
                volume=random.randint(10000, 500000),
                avg_volume=random.randint(50000, 200000),
                timestamp=timestamp,
                market_status='OPEN',
                data_source='KOTAK_NEO',
                fetch_status='SUCCESS'
            )
            
            db.session.add(quote)
            created_quotes += 1
    
    db.session.commit()
    logger.info(f"Created {created_quotes} sample quotes")
    return created_quotes

def create_sample_etf_signals(users):
    """Create sample ETF signal trades"""
    if len(users) < 2:
        logger.error("Need at least 2 users to create signals")
        return 0
    
    admin_user = users[0]  # First user is admin
    target_users = users[1:]  # Rest are target users
    
    signals_data = [
        {
            'symbol': 'NIFTYBEES',
            'etf_name': 'Nippon India ETF Nifty BeES',
            'signal_type': 'BUY',
            'entry_price': 245.50,
            'target_price': 260.00,
            'stop_loss': 235.00,
            'quantity': 100,
            'trade_title': 'NIFTY ETF - Bullish Breakout',
            'priority': 'HIGH'
        },
        {
            'symbol': 'BANKBEES',
            'etf_name': 'Nippon India ETF Bank BeES',
            'signal_type': 'BUY',
            'entry_price': 520.75,
            'target_price': 545.00,
            'stop_loss': 505.00,
            'quantity': 50,
            'trade_title': 'Bank ETF - Sector Rotation',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'GOLDSHARE',
            'etf_name': 'Goldman Sachs Gold ETF',
            'signal_type': 'SELL',
            'entry_price': 4850.00,
            'target_price': 4720.00,
            'stop_loss': 4920.00,
            'quantity': 10,
            'trade_title': 'Gold ETF - Profit Booking',
            'priority': 'MEDIUM'
        },
        {
            'symbol': 'ITBEES',
            'etf_name': 'Nippon India ETF IT BeES',
            'signal_type': 'BUY',
            'entry_price': 385.25,
            'target_price': 405.00,
            'stop_loss': 370.00,
            'quantity': 75,
            'trade_title': 'IT ETF - Tech Recovery',
            'priority': 'HIGH'
        },
        {
            'symbol': 'PSUBNKBEES',
            'etf_name': 'Nippon India ETF PSU Bank BeES',
            'signal_type': 'BUY',
            'entry_price': 15.80,
            'target_price': 17.50,
            'stop_loss': 14.90,
            'quantity': 500,
            'trade_title': 'PSU Bank ETF - Value Pick',
            'priority': 'MEDIUM'
        }
    ]
    
    created_signals = 0
    
    # Create ETF Signal Trades
    for signal_data in signals_data:
        for user in target_users:
            entry_price = Decimal(str(signal_data['entry_price']))
            invested_amount = entry_price * signal_data['quantity']
            
            # Get current price from latest quote
            latest_quote = RealtimeQuote.query.filter_by(
                symbol=signal_data['symbol']
            ).order_by(RealtimeQuote.timestamp.desc()).first()
            
            current_price = latest_quote.current_price if latest_quote else entry_price
            
            etf_signal = ETFSignalTrade(
                user_id=user.id,
                assigned_by_user_id=admin_user.id,
                symbol=signal_data['symbol'],
                etf_name=signal_data['etf_name'],
                trading_symbol=f"{signal_data['symbol']}-EQ",
                token=f"TK{random.randint(10000, 99999)}",
                exchange='NSE',
                signal_type=signal_data['signal_type'],
                quantity=signal_data['quantity'],
                entry_price=entry_price,
                current_price=current_price,
                target_price=Decimal(str(signal_data['target_price'])) if signal_data.get('target_price') else None,
                stop_loss=Decimal(str(signal_data['stop_loss'])) if signal_data.get('stop_loss') else None,
                invested_amount=invested_amount,
                current_value=current_price * signal_data['quantity'],
                trade_title=signal_data['trade_title'],
                trade_description=f"ETF {signal_data['signal_type']} signal for {signal_data['etf_name']}",
                priority=signal_data['priority'],
                status='ACTIVE',
                position_type='LONG' if signal_data['signal_type'] == 'BUY' else 'SHORT',
                entry_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                last_price_update=datetime.utcnow()
            )
            
            # Calculate P&L
            etf_signal.calculate_pnl()
            
            db.session.add(etf_signal)
            created_signals += 1
    
    # Create Admin Trade Signals
    for signal_data in signals_data:
        for user in target_users:
            admin_signal = AdminTradeSignal(
                admin_user_id=admin_user.id,
                target_user_id=user.id,
                symbol=signal_data['symbol'],
                trading_symbol=f"{signal_data['symbol']}-EQ",
                token=f"TK{random.randint(10000, 99999)}",
                exchange='NSE',
                signal_type=signal_data['signal_type'],
                entry_price=Decimal(str(signal_data['entry_price'])),
                target_price=Decimal(str(signal_data['target_price'])) if signal_data.get('target_price') else None,
                stop_loss=Decimal(str(signal_data['stop_loss'])) if signal_data.get('stop_loss') else None,
                quantity=signal_data['quantity'],
                signal_title=signal_data['trade_title'],
                signal_description=f"Admin signal for {signal_data['etf_name']}",
                priority=signal_data['priority'],
                status='ACTIVE',
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            # Set current price from latest quote
            latest_quote = RealtimeQuote.query.filter_by(
                symbol=signal_data['symbol']
            ).order_by(RealtimeQuote.timestamp.desc()).first()
            
            if latest_quote:
                admin_signal.current_price = latest_quote.current_price
                if admin_signal.entry_price:
                    change_pct = ((float(latest_quote.current_price) - float(admin_signal.entry_price)) / float(admin_signal.entry_price)) * 100
                    admin_signal.change_percent = Decimal(str(round(change_pct, 2)))
                admin_signal.last_update_time = datetime.utcnow()
            
            db.session.add(admin_signal)
            created_signals += 1
    
    db.session.commit()
    logger.info(f"Created {created_signals} sample signals")
    return created_signals

def main():
    """Main function to populate demo data"""
    with app.app_context():
        try:
            logger.info("Starting demo data population...")
            
            # Create all tables
            db.create_all()
            logger.info("Database tables created/verified")
            
            # Create demo users
            users = create_demo_users()
            logger.info(f"Created/verified {len(users)} users")
            
            # Create sample quotes
            quotes_count = create_sample_quotes()
            logger.info(f"Created {quotes_count} sample quotes")
            
            # Create sample signals
            signals_count = create_sample_etf_signals(users)
            logger.info(f"Created {signals_count} sample signals")
            
            logger.info("Demo data population completed successfully!")
            
            # Print summary
            print("\n" + "="*50)
            print("DEMO DATA POPULATION SUMMARY")
            print("="*50)
            print(f"Users created: {len(users)}")
            print(f"Quotes created: {quotes_count}")
            print(f"Signals created: {signals_count}")
            print("\nYou can now test the trading signals management system!")
            print("Admin user: ADMIN001")
            print("Test users: USER001, USER002, USER003, USER004")
            print("="*50)
            
        except Exception as e:
            logger.error(f"Error populating demo data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()