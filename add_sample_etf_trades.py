
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
        # Get or create a user with UCC "ZHZ3J" (matching your existing user)
        user = User.query.filter_by(ucc="ZHZ3J").first()
        if not user:
            # Create a sample user with UCC ZHZ3J
            user = User(
                ucc="ZHZ3J",
                mobile_number="9876543210",
                greeting_name="Test User",
                user_id="ZHZ3J",
                client_code="ZHZ3J",
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created sample user: {user.ucc}")
        
        # Clear existing ETF signal trades for this user (for testing)
        ETFSignalTrade.query.filter_by(user_id=user.id).delete()
        
        # Sample ETF trade data with realistic values
        sample_trades = [
            {
                'symbol': 'NIFTYBEES',
                'etf_name': 'Nippon India ETF Nifty BeES',
                'trading_symbol': 'NIFTYBEES-EQ',
                'token': '40164',
                'signal_type': 'BUY',
                'quantity': 200,
                'entry_price': 227.00,
                'current_price': 225.70,
                'target_price': 254.26,
                'stop_loss': 215.00,
                'trade_title': 'BUY NIFTYBEES - Index ETF Long',
                'trade_description': 'Strong support at current levels, expecting bounce back',
                'priority': 'HIGH',
                'change_pct': '-0.57%',
                'tp_return': '₹5,452'
            },
            {
                'symbol': 'GOLDBEES',
                'etf_name': 'Goldman Sachs Gold BeeS',
                'trading_symbol': 'GOLDBEES-EQ',
                'token': '40165',
                'signal_type': 'BUY',
                'quantity': 500,
                'entry_price': 40.23,
                'current_price': 40.00,
                'target_price': 45.79,
                'stop_loss': 37.50,
                'trade_title': 'BUY GOLDBEES - Gold ETF',
                'trade_description': 'Gold showing strength, good hedge against inflation',
                'priority': 'MEDIUM',
                'change_pct': '-0.57%',
                'tp_return': '₹2,780'
            },
            {
                'symbol': 'BANKBEES',
                'etf_name': 'Nippon India ETF Bank BeES',
                'trading_symbol': 'BANKBEES-EQ',
                'token': '40166',
                'signal_type': 'BUY',
                'quantity': 100,
                'entry_price': 46.15,
                'current_price': 45.00,
                'target_price': 52.26,
                'stop_loss': 42.00,
                'trade_title': 'BUY BANKBEES - Banking Sector ETF',
                'trade_description': 'Banking sector oversold, expecting recovery',
                'priority': 'MEDIUM',
                'change_pct': '-2.49%',
                'tp_return': '₹611'
            },
            {
                'symbol': 'SILVERBEES',
                'etf_name': 'Nippon India ETF Silver BeES',
                'trading_symbol': 'SILVERBEES-EQ',
                'token': '40167',
                'signal_type': 'BUY',
                'quantity': 607,
                'entry_price': 93.00,
                'current_price': 104.29,
                'target_price': 110.00,
                'stop_loss': 88.00,
                'trade_title': 'BUY SILVERBEES - Silver ETF Profit',
                'trade_description': 'Silver rally continues, good momentum',
                'priority': 'HIGH',
                'change_pct': '+12.13%',
                'tp_return': '₹3,459'
            },
            {
                'symbol': 'ITBEES',
                'etf_name': 'Nippon India ETF IT BeES',
                'trading_symbol': 'ITBEES-EQ',
                'token': '40168',
                'signal_type': 'BUY',
                'quantity': 1560,
                'entry_price': 64.25,
                'current_price': 62.36,
                'target_price': 69.00,
                'stop_loss': 60.00,
                'trade_title': 'BUY ITBEES - IT Sector Recovery',
                'trade_description': 'IT sector showing signs of recovery',
                'priority': 'MEDIUM',
                'change_pct': '-2.94%',
                'tp_return': '₹7,410'
            },
            {
                'symbol': 'JUNIORBEES',
                'etf_name': 'Nippon India ETF Junior BeES',
                'trading_symbol': 'JUNIORBEES-EQ',
                'token': '40169',
                'signal_type': 'BUY',
                'quantity': 1600,
                'entry_price': 95.78,
                'current_price': 96.24,
                'target_price': 105.00,
                'stop_loss': 90.00,
                'trade_title': 'BUY JUNIORBEES - Mid Cap Opportunity',
                'trade_description': 'Mid cap stocks showing strength',
                'priority': 'LOW',
                'change_pct': '+0.48%',
                'tp_return': '₹14,752'
            },
            {
                'symbol': 'PHARMABEES',
                'etf_name': 'Nippon India ETF Pharma BeES',
                'trading_symbol': 'PHARMABEES-EQ',
                'token': '40170',
                'signal_type': 'BUY',
                'quantity': 4500,
                'entry_price': 22.70,
                'current_price': 22.25,
                'target_price': 25.42,
                'stop_loss': 21.00,
                'trade_title': 'BUY PHARMABEES - Healthcare Sector',
                'trade_description': 'Pharma sector undervalued, good long term',
                'priority': 'MEDIUM',
                'change_pct': '-1.98%',
                'tp_return': '₹12,240'
            },
            {
                'symbol': 'CONSUMERBEES',
                'etf_name': 'Nippon India ETF Consumption BeES',
                'trading_symbol': 'CONSUMERBEES-EQ',
                'token': '40171',
                'signal_type': 'BUY',
                'quantity': 120,
                'entry_price': 73.42,
                'current_price': 71.60,
                'target_price': 82.14,
                'stop_loss': 69.00,
                'trade_title': 'BUY CONSUMERBEES - Consumer Goods',
                'trade_description': 'Consumer sector showing resilience',
                'priority': 'LOW',
                'change_pct': '-2.48%',
                'tp_return': '₹1,046'
            },
            {
                'symbol': 'LIQUIDBEES',
                'etf_name': 'Nippon India ETF Liquid BeES',
                'trading_symbol': 'LIQUIDBEES-EQ',
                'token': '40172',
                'signal_type': 'BUY',
                'quantity': 472,
                'entry_price': 1341.00,
                'current_price': 1362.00,
                'target_price': 1389.00,
                'stop_loss': 1320.00,
                'trade_title': 'BUY LIQUIDBEES - Liquid Fund ETF',
                'trade_description': 'Safe liquid investment option',
                'priority': 'LOW',
                'change_pct': '+1.57%',
                'tp_return': '₹22,656'
            },
            {
                'symbol': 'PSUBNKBEES',
                'etf_name': 'Nippon India ETF PSU Bank BeES',
                'trading_symbol': 'PSUBNKBEES-EQ',
                'token': '40173',
                'signal_type': 'BUY',
                'quantity': 300,
                'entry_price': 85.44,
                'current_price': 104.29,
                'target_price': 115.00,
                'stop_loss': 80.00,
                'trade_title': 'BUY PSUBNKBEES - PSU Banking Rally',
                'trade_description': 'PSU banks showing strong momentum',
                'priority': 'HIGH',
                'change_pct': '+22.04%',
                'tp_return': '₹8,868'
            }
        ]
        
        created_trades = []
        total_investment = 0.0
        total_current_value = 0.0
        total_pnl = 0.0
        profit_trades = 0
        loss_trades = 0
        
        for i, trade_data in enumerate(sample_trades):
            # Calculate values
            entry_price = float(trade_data['entry_price'])
            current_price = float(trade_data['current_price'])
            quantity = int(trade_data['quantity'])
            target_price = float(trade_data['target_price'])
            
            invested_amount = entry_price * quantity
            current_value = current_price * quantity
            pnl_amount = current_value - invested_amount
            pnl_percent = (pnl_amount / invested_amount) * 100 if invested_amount > 0 else 0
            
            # Track profit/loss
            if pnl_amount > 0:
                profit_trades += 1
            elif pnl_amount < 0:
                loss_trades += 1
            
            # Accumulate totals
            total_investment += invested_amount
            total_current_value += current_value
            total_pnl += pnl_amount
            
            # Create entry date (random within last 60 days)
            days_ago = random.randint(1, 60)
            entry_date = datetime.utcnow() - timedelta(days=days_ago)
            
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
                quantity=quantity,
                entry_price=entry_price,
                current_price=current_price,
                target_price=target_price,
                stop_loss=trade_data.get('stop_loss', entry_price * 0.95),
                invested_amount=invested_amount,
                current_value=current_value,
                pnl_amount=pnl_amount,
                pnl_percent=pnl_percent,
                trade_title=trade_data['trade_title'],
                trade_description=trade_data['trade_description'],
                priority=trade_data['priority'],
                status='ACTIVE',
                position_type='LONG',
                change_pct=trade_data['change_pct'],
                tp_return=trade_data['tp_return'],
                entry_date=entry_date,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_price_update=datetime.utcnow()
            )
            
            db.session.add(trade)
            created_trades.append(trade)
        
        # Commit all trades
        db.session.commit()
        
        print(f"✅ Created {len(created_trades)} sample ETF signal trades for user {user.ucc}")
        
        # Print summary
        return_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0.0
        
        print(f"\n📊 Portfolio Summary:")
        print(f"💰 Total Investment: ₹{total_investment:,.2f}")
        print(f"💵 Current Value: ₹{total_current_value:,.2f}")
        print(f"📈 Total P&L: ₹{total_pnl:,.2f}")
        print(f"📊 Return %: {return_percent:.2f}%")
        print(f"✅ Profit Trades: {profit_trades}")
        print(f"❌ Loss Trades: {loss_trades}")
        
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
        print(f"❌ Error creating sample trades: {str(e)}")
        import traceback
        traceback.print_exc()
