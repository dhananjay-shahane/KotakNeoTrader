#!/usr/bin/env python3
"""
Script to create sample ETF positions for testing the ETF Signals page
"""
from app import app, db
from models_etf import ETFPosition
from datetime import datetime, timedelta
import random

def create_sample_etf_positions():
    """Create sample ETF positions for demonstration"""
    with app.app_context():
        # Clear existing ETF positions (for testing)
        ETFPosition.query.delete()
        
        # Sample ETF data with realistic prices
        sample_etfs = [
            {
                'etf_symbol': 'NIFTYBEES',
                'trading_symbol': 'NIFTYBEES-EQ',
                'token': '15083',
                'exchange': 'NSE',
                'quantity': 100,
                'entry_price': 195.50,
                'target_price': 210.00,
                'current_price': 202.75,
                'entry_date': datetime.now().date() - timedelta(days=15)
            },
            {
                'etf_symbol': 'GOLDBEES',
                'trading_symbol': 'GOLDBEES-EQ',
                'token': '1660',
                'exchange': 'NSE',
                'quantity': 200,
                'entry_price': 43.25,
                'target_price': 47.50,
                'current_price': 44.80,
                'entry_date': datetime.now().date() - timedelta(days=30)
            },
            {
                'etf_symbol': 'BANKBEES',
                'trading_symbol': 'BANKBEES-EQ',
                'token': '2800',
                'exchange': 'NSE',
                'quantity': 50,
                'entry_price': 385.75,
                'target_price': 420.00,
                'current_price': 391.20,
                'entry_date': datetime.now().date() - timedelta(days=7)
            },
            {
                'etf_symbol': 'JUNIORBEES',
                'trading_symbol': 'JUNIORBEES-EQ',
                'token': '583',
                'exchange': 'NSE',
                'quantity': 75,
                'entry_price': 298.60,
                'target_price': 315.00,
                'current_price': 305.25,
                'entry_date': datetime.now().date() - timedelta(days=20)
            },
            {
                'etf_symbol': 'LIQUIDBEES',
                'trading_symbol': 'LIQUIDBEES-EQ',
                'token': '1023',
                'exchange': 'NSE',
                'quantity': 500,
                'entry_price': 999.85,
                'target_price': 1000.50,
                'current_price': 1000.12,
                'entry_date': datetime.now().date() - timedelta(days=5)
            }
        ]
        
        # Assume user_id = 1 (adjust based on your user system)
        user_id = 1
        
        for etf_data in sample_etfs:
            position = ETFPosition()
            position.user_id = user_id
            position.etf_symbol = etf_data['etf_symbol']
            position.trading_symbol = etf_data['trading_symbol']
            position.token = etf_data['token']
            position.exchange = etf_data['exchange']
            position.entry_date = etf_data['entry_date']
            position.quantity = etf_data['quantity']
            position.entry_price = etf_data['entry_price']
            position.target_price = etf_data.get('target_price')
            position.current_price = etf_data['current_price']
            position.last_update_time = datetime.utcnow()
            position.position_type = 'LONG'
            position.notes = f'Sample position for {etf_data["etf_symbol"]}'
            position.is_active = True
            
            db.session.add(position)
        
        db.session.commit()
        print(f"✅ Created {len(sample_etfs)} sample ETF positions")
        
        # Verify creation
        positions = ETFPosition.query.all()
        print(f"📊 Total ETF positions in database: {len(positions)}")
        
        for pos in positions:
            profit_loss = (pos.current_price - pos.entry_price) * pos.quantity if pos.current_price else 0
            print(f"   {pos.etf_symbol}: {pos.quantity} @ ₹{pos.entry_price} → ₹{pos.current_price} (P&L: ₹{profit_loss:.2f})")

if __name__ == '__main__':
    create_sample_etf_positions()