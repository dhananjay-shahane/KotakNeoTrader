"""
Create sample ETF signals for testing the trading signal management system
This will create real signals that appear in the ETF signals page
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from models_etf import ETFSignalTrade
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_user():
    """Get existing user or create a demo user"""
    user = User.query.first()
    if not user:
        user = User(
            ucc='DEMO001',
            mobile_number='9999999999',
            greeting_name='Demo User',
            user_id='demo001',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created demo user: {user.greeting_name}")
    else:
        logger.info(f"Using existing user: {user.greeting_name}")
    return user

def create_etf_signals():
    """Create sample ETF signals"""
    user = get_or_create_user()
    
    # Sample ETF signals data
    signals_data = [
        {
            'symbol': 'NIFTYBEES',
            'etf_name': 'Nippon India ETF Nifty BeES',
            'signal_type': 'BUY',
            'entry_price': 245.50,
            'current_price': 248.75,
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
            'current_price': 525.30,
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
            'current_price': 4825.00,
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
            'current_price': 392.80,
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
            'current_price': 16.25,
            'target_price': 17.50,
            'stop_loss': 14.90,
            'quantity': 500,
            'trade_title': 'PSU Bank ETF - Value Pick',
            'priority': 'MEDIUM'
        }
    ]
    
    created_signals = 0
    
    for signal_data in signals_data:
        entry_price = Decimal(str(signal_data['entry_price']))
        current_price = Decimal(str(signal_data['current_price']))
        invested_amount = entry_price * signal_data['quantity']
        current_value = current_price * signal_data['quantity']
        
        etf_signal = ETFSignalTrade(
            user_id=user.id,
            assigned_by_user_id=user.id,  # Self-assigned for demo
            symbol=signal_data['symbol'],
            etf_name=signal_data['etf_name'],
            trading_symbol=f"{signal_data['symbol']}-EQ",
            token=f"TK{12345 + created_signals}",
            exchange='NSE',
            signal_type=signal_data['signal_type'],
            quantity=signal_data['quantity'],
            entry_price=entry_price,
            current_price=current_price,
            target_price=Decimal(str(signal_data['target_price'])) if signal_data.get('target_price') else None,
            stop_loss=Decimal(str(signal_data['stop_loss'])) if signal_data.get('stop_loss') else None,
            invested_amount=invested_amount,
            current_value=current_value,
            trade_title=signal_data['trade_title'],
            trade_description=f"ETF {signal_data['signal_type']} signal for {signal_data['etf_name']}",
            priority=signal_data['priority'],
            status='ACTIVE',
            position_type='LONG' if signal_data['signal_type'] == 'BUY' else 'SHORT',
            entry_date=datetime.utcnow() - timedelta(days=created_signals + 1),
            last_price_update=datetime.utcnow()
        )
        
        # Calculate P&L
        etf_signal.calculate_pnl()
        
        db.session.add(etf_signal)
        created_signals += 1
        logger.info(f"Created signal: {signal_data['symbol']} - {signal_data['signal_type']}")
    
    db.session.commit()
    logger.info(f"Created {created_signals} ETF signals")
    return created_signals

def main():
    """Main function"""
    with app.app_context():
        try:
            logger.info("Creating sample ETF signals...")
            
            # Create tables if needed
            db.create_all()
            
            # Clear existing signals
            ETFSignalTrade.query.delete()
            db.session.commit()
            logger.info("Cleared existing signals")
            
            # Create new signals
            signals_count = create_etf_signals()
            
            logger.info("Sample ETF signals created successfully!")
            print(f"\n✅ Created {signals_count} ETF signals")
            print("You can now view them on the ETF signals page")
            
        except Exception as e:
            logger.error(f"Error creating signals: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()