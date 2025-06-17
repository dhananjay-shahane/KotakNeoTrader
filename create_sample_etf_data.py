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
        
        # Sample ETF data matching the screenshot format
        sample_etfs = [
            {
                'etf_symbol': 'IETF',
                'trading_symbol': 'IETF-EQ',
                'token': '40164',
                'exchange': 'NSE',
                'quantity': 500,
                'entry_price': 47.13,
                'target_price': 52.75,
                'current_price': 40.68,
                'entry_date': datetime(2024, 12, 13).date()
            },
            {
                'etf_symbol': 'CONSUMERBEES',
                'trading_symbol': 'CONSUMERBEES-EQ',
                'token': '155443',
                'exchange': 'NSE',
                'quantity': 0,
                'entry_price': 0.0,
                'target_price': 0.0,
                'current_price': 126.99,
                'entry_date': datetime(2024, 6, 20).date()
            },
            {
                'etf_symbol': 'SILVERBEES',
                'trading_symbol': 'SILVERBEES-EQ',
                'token': '106550',
                'exchange': 'NSE',
                'quantity': 1100,
                'entry_price': 86.85,
                'target_price': 0.0,
                'current_price': 109.65,
                'entry_date': datetime(2024, 5, 22).date()
            },
            {
                'etf_symbol': 'GOLDBEES',
                'trading_symbol': 'GOLDBEES-EQ',
                'token': '84250',
                'exchange': 'NSE',
                'quantity': 1560,
                'entry_price': 64.25,
                'target_price': 66.50,
                'current_price': 82.82,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'PSUBNKBEES',
                'trading_symbol': 'PSUBNKBEES-EQ',
                'token': '799534',
                'exchange': 'NSE',
                'quantity': 50,
                'entry_price': 39.12,
                'target_price': 39016.0,
                'current_price': 72.61,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'CONSUMERBEES',
                'trading_symbol': 'CONSUMERBEES-EQ',
                'token': '122145',
                'exchange': 'NSE',
                'quantity': 360,
                'entry_price': 128.2,
                'target_price': 143.56,
                'current_price': 126.99,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'HDFCNIFETF',
                'trading_symbol': 'HDFCNIFETF-EQ',
                'token': '25254',
                'exchange': 'NSE',
                'quantity': 2800,
                'entry_price': 43.1,
                'target_price': 68568.0,
                'current_price': 23.85,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'PHARMABEES',
                'trading_symbol': 'PHARMABEES-EQ',
                'token': '24140',
                'exchange': 'NSE',
                'quantity': 4500,
                'entry_price': 22.7,
                'target_price': 25.42,
                'current_price': 22.33,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'ITBEES',
                'trading_symbol': 'ITBEES-EQ',
                'token': '59533',
                'exchange': 'NSE',
                'quantity': 1,
                'entry_price': 731.42,
                'target_price': 881.49,
                'current_price': 724.1,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'CONSUMERBEES',
                'trading_symbol': 'CONSUMERBEES-EQ',
                'token': '162165',
                'exchange': 'NSE',
                'quantity': 472,
                'entry_price': 124.1,
                'target_price': 138.95,
                'current_price': 126.99,
                'entry_date': datetime(2024, 6, 20).date()
            },
            {
                'etf_symbol': 'SILVERBEES',
                'trading_symbol': 'SILVERBEES-EQ',
                'token': '106326',
                'exchange': 'NSE',
                'quantity': 300,
                'entry_price': 84.44,
                'target_price': 0.0,
                'current_price': 109.65,
                'entry_date': datetime(2024, 6, 23).date()
            },
            {
                'etf_symbol': 'JUNIORBEES',
                'trading_symbol': 'JUNIORBEES-EQ',
                'token': '59353',
                'exchange': 'NSE',
                'quantity': 130,
                'entry_price': 293.96,
                'target_price': 627.64,
                'current_price': 292.11,
                'entry_date': datetime(2024, 6, 24).date()
            },
            {
                'etf_symbol': 'NIFTYBEES',
                'trading_symbol': 'NIFTYBEES-EQ',
                'token': '264119',
                'exchange': 'NSE',
                'quantity': 400,
                'entry_price': 245.48,
                'target_price': 0.0,
                'current_price': 278.76,
                'entry_date': datetime(2024, 6, 28).date()
            },
            {
                'etf_symbol': 'LIQUIDETF',
                'trading_symbol': 'LIQUIDETF-EQ',
                'token': '40079',
                'exchange': 'NSE',
                'quantity': 4000,
                'entry_price': 25.18,
                'target_price': 0.0,
                'current_price': 26.09,
                'entry_date': datetime(2024, 7, 24).date()
            },
            {
                'etf_symbol': 'AUBANK',
                'trading_symbol': 'AUBANK-EQ',
                'token': '25347',
                'exchange': 'NSE',
                'quantity': 5000,
                'entry_price': 23.2,
                'target_price': 0.0,
                'current_price': 23.86,
                'entry_date': datetime(2024, 7, 14).date()
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