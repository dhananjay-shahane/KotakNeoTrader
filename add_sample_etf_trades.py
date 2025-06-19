#!/usr/bin/env python3
"""
Script to add sample ETF signal trades to the database
"""
from app import app, db
from models import User
from models_etf import ETFSignalTrade, UserNotification
from datetime import datetime, timedelta
import random
import logging

def create_sample_etf_signal_trades():
    """Create 10 sample ETF signal trades assigned by admin to users"""
    with app.app_context():
        try:
            # Get all users
            users = User.query.all()
            if not users:
                print("❌ No users found in database. Please create users first.")
                return False

            # Use first user as admin (or create admin if needed)
            admin_user = users[0]
            target_users = users[1:] if len(users) > 1 else users  # Other users as targets

            print(f"🔧 Using admin user: {admin_user.ucc}")
            print(f"📊 Target users: {[u.ucc for u in target_users]}")

            # Sample ETF data
            sample_etfs = [
                {
                    'symbol': 'NIFTYBEES',
                    'etf_name': 'Nippon India ETF Nifty BeES',
                    'entry_price': 185.50,
                    'current_price': 192.30,
                    'signal_type': 'BUY',
                    'quantity': 100,
                    'target_price': 200.00,
                    'stop_loss': 180.00,
                    'trade_title': 'NIFTYBEES Long Position',
                    'trade_description': 'Bullish on Nifty 50 index with target of 200'
                },
                {
                    'symbol': 'BANKBEES',
                    'etf_name': 'Nippon India ETF Bank BeES',
                    'entry_price': 425.75,
                    'current_price': 441.20,
                    'signal_type': 'BUY',
                    'quantity': 50,
                    'target_price': 460.00,
                    'stop_loss': 410.00,
                    'trade_title': 'BANKBEES Banking Sector Play',
                    'trade_description': 'Banking sector recovery trade'
                },
                {
                    'symbol': 'GOLDBEES',
                    'etf_name': 'Nippon India ETF Gold BeES',
                    'entry_price': 42.80,
                    'current_price': 41.95,
                    'signal_type': 'BUY',
                    'quantity': 200,
                    'target_price': 45.00,
                    'stop_loss': 40.00,
                    'trade_title': 'GOLDBEES Safe Haven Trade',
                    'trade_description': 'Gold hedge against market volatility'
                },
                {
                    'symbol': 'ITBEES',
                    'etf_name': 'Nippon India ETF IT BeES',
                    'entry_price': 38.65,
                    'current_price': 39.80,
                    'signal_type': 'BUY',
                    'quantity': 150,
                    'target_price': 42.00,
                    'stop_loss': 36.00,
                    'trade_title': 'ITBEES Technology Sector',
                    'trade_description': 'IT sector momentum play'
                },
                {
                    'symbol': 'JUNIORBEES',
                    'etf_name': 'Nippon India ETF Junior BeES',
                    'entry_price': 325.40,
                    'current_price': 318.75,
                    'signal_type': 'BUY',
                    'quantity': 30,
                    'target_price': 340.00,
                    'stop_loss': 310.00,
                    'trade_title': 'JUNIORBEES Mid-cap Exposure',
                    'trade_description': 'Mid-cap index exposure for growth'
                },
                {
                    'symbol': 'PSUBNKBEES',
                    'etf_name': 'Nippon India ETF PSU Bank BeES',
                    'entry_price': 18.25,
                    'current_price': 19.10,
                    'signal_type': 'BUY',
                    'quantity': 500,
                    'target_price': 21.00,
                    'stop_loss': 17.00,
                    'trade_title': 'PSUBNKBEES PSU Bank Recovery',
                    'trade_description': 'PSU banking sector turnaround story'
                },
                {
                    'symbol': 'LIQUIDBEES',
                    'etf_name': 'Nippon India ETF Liquid BeES',
                    'entry_price': 1000.15,
                    'current_price': 1000.45,
                    'signal_type': 'BUY',
                    'quantity': 10,
                    'target_price': 1001.00,
                    'stop_loss': 999.50,
                    'trade_title': 'LIQUIDBEES Cash Management',
                    'trade_description': 'Liquid fund for cash parking'
                },
                {
                    'symbol': 'PHARMABEES',
                    'etf_name': 'Nippon India ETF Pharma BeES',
                    'entry_price': 1245.60,
                    'current_price': 1289.30,
                    'signal_type': 'BUY',
                    'quantity': 8,
                    'target_price': 1350.00,
                    'stop_loss': 1200.00,
                    'trade_title': 'PHARMABEES Healthcare Play',
                    'trade_description': 'Pharma sector defensive play'
                },
                {
                    'symbol': 'CONSUMPTION',
                    'etf_name': 'Nippon India ETF Consumption',
                    'entry_price': 89.75,
                    'current_price': 87.20,
                    'signal_type': 'BUY',
                    'quantity': 100,
                    'target_price': 95.00,
                    'stop_loss': 85.00,
                    'trade_title': 'CONSUMPTION Consumer Theme',
                    'trade_description': 'Consumer discretionary sector bet'
                },
                {
                    'symbol': 'INFRABES',
                    'etf_name': 'Nippon India ETF Infrastructure BeES',
                    'entry_price': 67.85,
                    'current_price': 71.25,
                    'signal_type': 'BUY',
                    'quantity': 120,
                    'target_price': 75.00,
                    'stop_loss': 65.00,
                    'trade_title': 'INFRABES Infrastructure Growth',
                    'trade_description': 'Infrastructure sector growth story'
                }
            ]

            created_trades = []
            created_notifications = []

            # Create trades for each user
            for i, etf_data in enumerate(sample_etfs):
                # Select target user (cycle through available users)
                target_user = target_users[i % len(target_users)]

                # Calculate invested amount
                invested_amount = etf_data['entry_price'] * etf_data['quantity']
                current_value = etf_data['current_price'] * etf_data['quantity']
                pnl_amount = current_value - invested_amount
                pnl_percent = (pnl_amount / invested_amount) * 100

                # Create ETF signal trade
                trade = ETFSignalTrade(
                    user_id=target_user.id,
                    assigned_by_user_id=admin_user.id,
                    symbol=etf_data['symbol'],
                    etf_name=etf_data['etf_name'],
                    trading_symbol=f"{etf_data['symbol']}-EQ",
                    token=f"TOKEN_{etf_data['symbol']}",
                    exchange='NSE',
                    signal_type=etf_data['signal_type'],
                    quantity=etf_data['quantity'],
                    entry_price=etf_data['entry_price'],
                    current_price=etf_data['current_price'],
                    target_price=etf_data['target_price'],
                    stop_loss=etf_data['stop_loss'],
                    invested_amount=invested_amount,
                    current_value=current_value,
                    pnl_amount=pnl_amount,
                    pnl_percent=pnl_percent,
                    trade_title=etf_data['trade_title'],
                    trade_description=etf_data['trade_description'],
                    priority='MEDIUM',
                    status='ACTIVE',
                    position_type='LONG',
                    change_pct=f"{pnl_percent:.2f}%",
                    tp_value=etf_data['target_price'] * etf_data['quantity'],
                    tp_return=f"{((etf_data['target_price'] - etf_data['entry_price']) / etf_data['entry_price'] * 100):.2f}%",
                    entry_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    created_at=datetime.utcnow(),
                    last_price_update=datetime.utcnow()
                )

                db.session.add(trade)
                db.session.flush()  # Get the trade ID
                created_trades.append(trade)

                # Create notification for target user
                notification = UserNotification(
                    user_id=target_user.id,
                    title=f"New ETF Signal: {etf_data['trade_title']}",
                    message=f"{etf_data['signal_type']} {etf_data['symbol']} @ ₹{etf_data['entry_price']} - {etf_data['trade_description']}",
                    notification_type='TRADE_SIGNAL',
                    priority='MEDIUM',
                    created_at=datetime.utcnow()
                )

                db.session.add(notification)
                created_notifications.append(notification)

            db.session.commit()

            # Calculate portfolio summary
            total_invested = sum(trade.invested_amount for trade in created_trades)
            total_current_value = sum(trade.current_value for trade in created_trades)
            total_pnl = total_current_value - total_invested
            return_percent = (total_pnl / total_invested) * 100

            profit_trades = len([t for t in created_trades if t.pnl_amount > 0])
            loss_trades = len([t for t in created_trades if t.pnl_amount < 0])

            print(f"✅ Created {len(created_trades)} sample ETF signal trades for user {target_users[0].ucc}")
            print(f"\n📊 Portfolio Summary:")
            print(f"💰 Total Investment: ₹{total_invested:,.2f}")
            print(f"💵 Current Value: ₹{total_current_value:,.2f}")
            print(f"📈 Total P&L: ₹{total_pnl:,.2f}")
            print(f"📊 Return %: {return_percent:.2f}%")
            print(f"✅ Profit Trades: {profit_trades}")
            print(f"❌ Loss Trades: {loss_trades}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample ETF signal trades: {str(e)}")
            logging.error(f"Error in create_sample_etf_signal_trades: {str(e)}")
            return False

if __name__ == "__main__":
    success = create_sample_etf_signal_trades()

    if success:
        print("\n🎉 Sample ETF trades added successfully!")
        print("You can now view them on the ETF Signals page: /etf-signals")
    else:
        print("\n❌ Failed to add sample ETF trades!")