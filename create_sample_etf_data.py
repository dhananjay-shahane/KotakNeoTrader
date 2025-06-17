
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
        
        # Sample ETF data matching the screenshot format with comprehensive dummy data
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
                'quantity': 472,
                'entry_price': 124.1,
                'target_price': 138.95,
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
                'target_price': 95.50,
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
                'target_price': 45.00,
                'current_price': 72.61,
                'entry_date': datetime(2024, 5, 16).date()
            },
            {
                'etf_symbol': 'HDFCNIFETF',
                'trading_symbol': 'HDFCNIFETF-EQ',
                'token': '25254',
                'exchange': 'NSE',
                'quantity': 2800,
                'entry_price': 43.1,
                'target_price': 48.50,
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
                'etf_symbol': 'JUNIORBEES',
                'trading_symbol': 'JUNIORBEES-EQ',
                'token': '59353',
                'exchange': 'NSE',
                'quantity': 130,
                'entry_price': 293.96,
                'target_price': 320.00,
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
                'target_price': 280.00,
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
                'target_price': 26.50,
                'current_price': 26.09,
                'entry_date': datetime(2024, 7, 24).date()
            },
            {
                'etf_symbol': 'BANKBEES',
                'trading_symbol': 'BANKBEES-EQ',
                'token': '25347',
                'exchange': 'NSE',
                'quantity': 200,
                'entry_price': 520.30,
                'target_price': 580.00,
                'current_price': 545.75,
                'entry_date': datetime(2024, 8, 14).date()
            },
            {
                'etf_symbol': 'PSUBANK',
                'trading_symbol': 'PSUBANK-EQ',
                'token': '155445',
                'exchange': 'NSE',
                'quantity': 800,
                'entry_price': 45.25,
                'target_price': 52.00,
                'current_price': 48.90,
                'entry_date': datetime(2024, 9, 10).date()
            },
            {
                'etf_symbol': 'FMCGBEES',
                'trading_symbol': 'FMCGBEES-EQ',
                'token': '789456',
                'exchange': 'NSE',
                'quantity': 150,
                'entry_price': 425.60,
                'target_price': 475.00,
                'current_price': 438.20,
                'entry_date': datetime(2024, 10, 5).date()
            },
            {
                'etf_symbol': 'AUTOBEES',
                'trading_symbol': 'AUTOBEES-EQ',
                'token': '963258',
                'exchange': 'NSE',
                'quantity': 300,
                'entry_price': 185.45,
                'target_price': 210.00,
                'current_price': 172.80,
                'entry_date': datetime(2024, 11, 8).date()
            },
            {
                'etf_symbol': 'REALTYBEES',
                'trading_symbol': 'REALTYBEES-EQ',
                'token': '741852',
                'exchange': 'NSE',
                'quantity': 500,
                'entry_price': 95.30,
                'target_price': 110.00,
                'current_price': 102.15,
                'entry_date': datetime(2024, 11, 15).date()
            },
            {
                'etf_symbol': 'ENERGYBEES',
                'trading_symbol': 'ENERGYBEES-EQ',
                'token': '852741',
                'exchange': 'NSE',
                'quantity': 250,
                'entry_price': 315.75,
                'target_price': 350.00,
                'current_price': 298.40,
                'entry_date': datetime(2024, 12, 1).date()
            },
            {
                'etf_symbol': 'SMALLCAP',
                'trading_symbol': 'SMALLCAP-EQ',
                'token': '159753',
                'exchange': 'NSE',
                'quantity': 75,
                'entry_price': 680.25,
                'target_price': 750.00,
                'current_price': 695.80,
                'entry_date': datetime(2024, 12, 10).date()
            },
            {
                'etf_symbol': 'MIDCAPBEES',
                'trading_symbol': 'MIDCAPBEES-EQ',
                'token': '357159',
                'exchange': 'NSE',
                'quantity': 100,
                'entry_price': 445.90,
                'target_price': 500.00,
                'current_price': 428.65,
                'entry_date': datetime(2024, 12, 12).date()
            },
            {
                'etf_symbol': 'INFRABEES',
                'trading_symbol': 'INFRABEES-EQ',
                'token': '951357',
                'exchange': 'NSE',
                'quantity': 350,
                'entry_price': 125.80,
                'target_price': 145.00,
                'current_price': 131.25,
                'entry_date': datetime(2024, 12, 14).date()
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
        
        # Verify creation and show summary
        positions = ETFPosition.query.all()
        print(f"📊 Total ETF positions in database: {len(positions)}")
        
        total_investment = 0
        total_current_value = 0
        profit_positions = 0
        loss_positions = 0
        
        print("\n📈 Portfolio Summary:")
        print("-" * 80)
        print(f"{'ETF':<15} {'Qty':<6} {'Entry':<8} {'Current':<8} {'P&L':<10} {'%Change':<8}")
        print("-" * 80)
        
        for pos in positions:
            investment = pos.entry_price * pos.quantity
            current_value = pos.current_price * pos.quantity if pos.current_price else 0
            profit_loss = current_value - investment
            percent_change = ((pos.current_price - pos.entry_price) / pos.entry_price * 100) if pos.current_price and pos.entry_price else 0
            
            total_investment += investment
            total_current_value += current_value
            
            if profit_loss > 0:
                profit_positions += 1
                status = "✅"
            elif profit_loss < 0:
                loss_positions += 1
                status = "❌"
            else:
                status = "➖"
            
            print(f"{pos.etf_symbol:<15} {pos.quantity:<6} ₹{pos.entry_price:<7.2f} ₹{pos.current_price:<7.2f} ₹{profit_loss:<9.2f} {percent_change:<7.2f}% {status}")
        
        total_pnl = total_current_value - total_investment
        total_return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        print("-" * 80)
        print(f"💰 Total Investment: ₹{total_investment:,.2f}")
        print(f"💵 Current Value: ₹{total_current_value:,.2f}")
        print(f"📈 Total P&L: ₹{total_pnl:,.2f}")
        print(f"📊 Return %: {total_return_percent:.2f}%")
        print(f"✅ Profit Positions: {profit_positions}")
        print(f"❌ Loss Positions: {loss_positions}")
        print(f"➖ Neutral Positions: {len(positions) - profit_positions - loss_positions}")

if __name__ == '__main__':
    create_sample_etf_positions()
