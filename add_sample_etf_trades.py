
#!/usr/bin/env python3
"""
Script to add sample ETF signal trades to the database
"""
from app import app, db
from models import User
from models_etf import ETFSignalTrade
from datetime import datetime, timedelta
import random

def create_sample_etf_trades():
    """Create sample ETF signal trades for demonstration"""
    with app.app_context():
        # Get or create a user
        user = User.query.first()
        if not user:
            # Create a sample user
            user = User(
                ucc="USER001",
                mobile_number="9876543210",
                greeting_name="Test User",
                user_id="user001",
                client_code="USER",
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created sample user: {user.ucc}")
        
        # Clear existing ETF signal trades (for testing)
        ETFSignalTrade.query.filter_by(user_id=user.id).delete()
        
        # Sample ETF trade data matching the CSV format
        sample_trades = [
            {
                'symbol': 'IETF',
                'etf_name': 'iShares Core Nifty ETF',
                'trading_symbol': 'IETF-EQ',
                'token': '40164',
                'signal_type': 'BUY',
                'quantity': 500,
                'entry_price': 47.13,
                'current_price': 40.68,
                'target_price': 52.75,
                'stop_loss': 42.50,
                'trade_title': 'BUY IETF - Undervalued Tech ETF',
                'trade_description': 'Strong support at current levels, expecting bounce back',
                'priority': 'HIGH',
                'change_pct': '-13.69%',
                'tp_return': '₹2,810'
            },
            {
                'symbol': 'CONSUMERBEES',
                'etf_name': 'Nippon India ETF Nifty FMCG',
                'trading_symbol': 'CONSUMERBEES-EQ',
                'token': '155443',
                'signal_type': 'BUY',
                'quantity': 472,
                'entry_price': 124.10,
                'current_price': 126.99,
                'target_price': 138.95,
                'stop_loss': 118.00,
                'trade_title': 'BUY CONSUMERBEES - FMCG Growth',
                'trade_description': 'Consumer sector showing strong fundamentals',
                'priority': 'MEDIUM',
                'change_pct': '2.33%',
                'tp_return': '₹7,024'
            },
            {
                'symbol': 'SILVERBEES',
                'etf_name': 'Nippon India ETF Gold BeES',
                'trading_symbol': 'SILVERBEES-EQ',
                'token': '106550',
                'signal_type': 'BUY',
                'quantity': 1100,
                'entry_price': 86.85,
                'current_price': 109.65,
                'target_price': 120.00,
                'stop_loss': 82.00,
                'trade_title': 'BUY SILVERBEES - Precious Metal Rally',
                'trade_description': 'Silver showing strong momentum, inflation hedge',
                'priority': 'HIGH',
                'change_pct': '26.24%',
                'tp_return': '₹25,080'
            },
            {
                'symbol': 'GOLDBEES',
                'etf_name': 'Nippon India ETF Gold BeES',
                'trading_symbol': 'GOLDBEES-EQ',
                'token': '84250',
                'signal_type': 'BUY',
                'quantity': 1560,
                'entry_price': 64.25,
                'current_price': 82.82,
                'target_price': 90.00,
                'stop_loss': 60.00,
                'trade_title': 'BUY GOLDBEES - Gold Momentum',
                'trade_description': 'Gold ETF showing strong uptrend, safe haven demand',
                'priority': 'MEDIUM',
                'change_pct': '28.93%',
                'tp_return': '₹28,968'
            },
            {
                'symbol': 'PSUBNKBEES',
                'etf_name': 'Nippon India ETF PSU Bank BeES',
                'trading_symbol': 'PSUBNKBEES-EQ',
                'token': '799534',
                'signal_type': 'BUY',
                'quantity': 50,
                'entry_price': 39.12,
                'current_price': 72.61,
                'target_price': 85.00,
                'stop_loss': 35.00,
                'trade_title': 'BUY PSUBNKBEES - Banking Sector Recovery',
                'trade_description': 'PSU banks showing strong recovery, govt support',
                'priority': 'HIGH',
                'change_pct': '85.60%',
                'tp_return': '₹1,674'
            },
            {
                'symbol': 'NIFTYBEES',
                'etf_name': 'Nippon India ETF Nifty BeES',
                'trading_symbol': 'NIFTYBEES-EQ',
                'token': '264119',
                'signal_type': 'BUY',
                'quantity': 400,
                'entry_price': 245.48,
                'current_price': 278.76,
                'target_price': 300.00,
                'stop_loss': 235.00,
                'trade_title': 'BUY NIFTYBEES - Market Leader',
                'trade_description': 'Nifty ETF tracking broad market, strong momentum',
                'priority': 'MEDIUM',
                'change_pct': '13.56%',
                'tp_return': '₹13,312'
            },
            {
                'symbol': 'BANKBEES',
                'etf_name': 'Nippon India ETF Bank BeES',
                'trading_symbol': 'BANKBEES-EQ',
                'token': '25347',
                'signal_type': 'BUY',
                'quantity': 200,
                'entry_price': 520.30,
                'current_price': 545.75,
                'target_price': 580.00,
                'stop_loss': 500.00,
                'trade_title': 'BUY BANKBEES - Banking Strength',
                'trade_description': 'Banking sector ETF showing consolidation, ready for breakout',
                'priority': 'MEDIUM',
                'change_pct': '4.89%',
                'tp_return': '₹5,090'
            },
            {
                'symbol': 'ITBEES',
                'etf_name': 'Nippon India ETF IT BeES',
                'trading_symbol': 'ITBEES-EQ',
                'token': '59533',
                'signal_type': 'BUY',
                'quantity': 1,
                'entry_price': 731.42,
                'current_price': 724.10,
                'target_price': 800.00,
                'stop_loss': 700.00,
                'trade_title': 'BUY ITBEES - Tech Recovery',
                'trade_description': 'IT sector showing signs of recovery, export demand',
                'priority': 'HIGH',
                'change_pct': '-1.00%',
                'tp_return': '₹75.90'
            },
            {
                'symbol': 'LIQUIDETF',
                'etf_name': 'Nippon India ETF Liquid BeES',
                'trading_symbol': 'LIQUIDETF-EQ',
                'token': '40079',
                'signal_type': 'BUY',
                'quantity': 4000,
                'entry_price': 25.18,
                'current_price': 26.09,
                'target_price': 27.00,
                'stop_loss': 24.50,
                'trade_title': 'BUY LIQUIDETF - Safe Parking',
                'trade_description': 'Liquid ETF for safe parking of funds with returns',
                'priority': 'LOW',
                'change_pct': '3.61%',
                'tp_return': '₹3,640'
            },
            {
                'symbol': 'JUNIORBEES',
                'etf_name': 'Nippon India ETF Junior BeES',
                'trading_symbol': 'JUNIORBEES-EQ',
                'token': '59353',
                'signal_type': 'SELL',
                'quantity': 130,
                'entry_price': 293.96,
                'current_price': 292.11,
                'target_price': 280.00,
                'stop_loss': 300.00,
                'trade_title': 'SELL JUNIORBEES - Profit Booking',
                'trade_description': 'Taking profits on midcap exposure, market volatility',
                'priority': 'MEDIUM',
                'change_pct': '-0.63%',
                'tp_return': '₹-1,805'
            }
        ]
        
        created_trades = []
        
        for trade_data in sample_trades:
            # Calculate invested amount
            invested_amount = float(trade_data['entry_price']) * int(trade_data['quantity'])
            
            # Create ETF signal trade
            trade = ETFSignalTrade(
                user_id=user.id,
                assigned_by_user_id=user.id,  # Self-assigned for demo
                symbol=trade_data['symbol'],
                etf_name=trade_data['etf_name'],
                trading_symbol=trade_data['trading_symbol'],
                token=trade_data['token'],
                exchange='NSE',
                signal_type=trade_data['signal_type'],
                quantity=trade_data['quantity'],
                entry_price=trade_data['entry_price'],
                current_price=trade_data['current_price'],
                target_price=trade_data.get('target_price'),
                stop_loss=trade_data.get('stop_loss'),
                invested_amount=invested_amount,
                trade_title=trade_data['trade_title'],
                trade_description=trade_data['trade_description'],
                priority=trade_data['priority'],
                position_type='LONG' if trade_data['signal_type'] == 'BUY' else 'SHORT',
                change_pct=trade_data['change_pct'],
                tp_return=trade_data['tp_return'],
                entry_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_price_update=datetime.utcnow()
            )
            
            # Calculate P&L
            trade.calculate_pnl()
            
            db.session.add(trade)
            created_trades.append(trade)
        
        db.session.commit()
        
        print(f"✅ Created {len(created_trades)} sample ETF signal trades for user {user.ucc}")
        
        # Display summary
        total_investment = sum(float(trade.invested_amount) for trade in created_trades)
        total_current_value = sum(float(trade.current_value or 0) for trade in created_trades)
        total_pnl = total_current_value - total_investment
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        print(f"\n📊 Portfolio Summary:")
        print(f"💰 Total Investment: ₹{total_investment:,.2f}")
        print(f"💵 Current Value: ₹{total_current_value:,.2f}")
        print(f"📈 Total P&L: ₹{total_pnl:,.2f}")
        print(f"📊 Return %: {return_percent:.2f}%")
        
        profit_trades = [t for t in created_trades if (t.pnl_amount or 0) > 0]
        loss_trades = [t for t in created_trades if (t.pnl_amount or 0) < 0]
        
        print(f"✅ Profit Trades: {len(profit_trades)}")
        print(f"❌ Loss Trades: {len(loss_trades)}")
        
        return True

if __name__ == '__main__':
    try:
        success = create_sample_etf_trades()
        if success:
            print("\n🎉 Sample ETF trades added successfully!")
            print("You can now view them on the ETF Signals page: /etf-signals")
        else:
            print("❌ Failed to add sample trades")
    except Exception as e:
        print(f"❌ Error: {e}")
