import logging
import pandas as pd
from datetime import datetime

class TradingFunctions:
    """Trading functions for Kotak Neo API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_data(self, client):
        """Get dashboard data including positions, holdings, and portfolio summary"""
        try:
            dashboard_data = {}
            
            # Get positions
            positions_response = client.positions()
            if positions_response and 'data' in positions_response:
                dashboard_data['positions'] = positions_response['data']
                dashboard_data['total_positions'] = len(positions_response['data'])
            else:
                dashboard_data['positions'] = []
                dashboard_data['total_positions'] = 0
            
            # Get holdings
            holdings_response = client.holdings()
            if holdings_response and 'data' in holdings_response:
                dashboard_data['holdings'] = holdings_response['data']
                dashboard_data['total_holdings'] = len(holdings_response['data'])
            else:
                dashboard_data['holdings'] = []
                dashboard_data['total_holdings'] = 0
            
            # Get limits
            try:
                limits_response = client.limits()
                if limits_response and 'data' in limits_response:
                    dashboard_data['limits'] = limits_response['data']
                else:
                    dashboard_data['limits'] = {}
            except:
                dashboard_data['limits'] = {}
            
            # Get order book
            try:
                orders_response = client.order_report()
                if orders_response and 'data' in orders_response:
                    dashboard_data['recent_orders'] = orders_response['data'][:5]  # Last 5 orders
                    dashboard_data['total_orders'] = len(orders_response['data'])
                else:
                    dashboard_data['recent_orders'] = []
                    dashboard_data['total_orders'] = 0
            except:
                dashboard_data['recent_orders'] = []
                dashboard_data['total_orders'] = 0
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    def get_positions(self, client):
        """Get current positions"""
        try:
            response = client.positions()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def get_holdings(self, client):
        """Get portfolio holdings"""
        try:
            response = client.holdings()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            self.logger.error(f"Error getting holdings: {str(e)}")
            return []
    
    def get_orders(self, client):
        """Get order book"""
        try:
            response = client.order_report()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            self.logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def place_order(self, client, order_data):
        """Place a new order based on Jupyter notebook implementation"""
        try:
            order_type = order_data.get('order_type', 'MARKET').upper()
            transaction_type = order_data.get('transaction_type', 'BUY').upper()
            trading_symbol = order_data.get('trading_symbol', '')
            quantity = str(order_data.get('quantity', 1))
            product = order_data.get('product', 'CNC')
            exchange_segment = order_data.get('exchange_segment', 'nse_cm')
            
            self.logger.info(f"📋 Placing {transaction_type} {order_type} order for {quantity} shares of {trading_symbol}")
            
            # Market Order
            if order_type in ['MARKET', 'MKT']:
                response = client.place_order(
                    exchange_segment=exchange_segment,
                    product=product,
                    price="0",  # Market order - price is 0
                    order_type="MKT",
                    quantity=quantity,
                    validity=order_data.get('validity', 'DAY'),
                    trading_symbol=trading_symbol,
                    transaction_type=transaction_type,
                    amo=order_data.get('amo', 'NO'),
                    disclosed_quantity=order_data.get('disclosed_quantity', '0'),
                    market_protection=order_data.get('market_protection', '0'),
                    pf=order_data.get('pf', 'N'),
                    trigger_price="0",
                    tag=order_data.get('tag', f"API_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                )
            
            # Limit Order
            elif order_type in ['LIMIT', 'L']:
                price = str(order_data.get('price', 0))
                response = client.place_order(
                    exchange_segment=exchange_segment,
                    product=product,
                    price=price,
                    order_type="L",
                    quantity=quantity,
                    validity=order_data.get('validity', 'DAY'),
                    trading_symbol=trading_symbol,
                    transaction_type=transaction_type,
                    amo=order_data.get('amo', 'NO'),
                    disclosed_quantity=order_data.get('disclosed_quantity', '0'),
                    market_protection=order_data.get('market_protection', '0'),
                    pf=order_data.get('pf', 'N'),
                    trigger_price="0",
                    tag=order_data.get('tag', f"API_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                )
            
            # Stop Loss Order
            elif order_type in ['STOPLOSS', 'SL']:
                price = str(order_data.get('price', 0))
                trigger_price = str(order_data.get('trigger_price', 0))
                response = client.place_order(
                    exchange_segment=exchange_segment,
                    product=product,
                    price=price,
                    order_type="SL",
                    quantity=quantity,
                    validity=order_data.get('validity', 'DAY'),
                    trading_symbol=trading_symbol,
                    transaction_type=transaction_type,
                    amo=order_data.get('amo', 'NO'),
                    disclosed_quantity=order_data.get('disclosed_quantity', '0'),
                    market_protection=order_data.get('market_protection', '0'),
                    pf=order_data.get('pf', 'N'),
                    trigger_price=trigger_price,
                    tag=order_data.get('tag', f"API_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                )
            
            else:
                return {'success': False, 'message': f'Unsupported order type: {order_type}'}
            
            if response and 'data' in response:
                self.logger.info("✅ Order placed successfully!")
                self.logger.info(f"Order Response: {response}")
                return {'success': True, 'data': response['data']}
            else:
                self.logger.error(f"❌ Order placement failed: {response}")
                return {'success': False, 'message': 'Order placement failed', 'response': response}
                
        except Exception as e:
            self.logger.error(f"❌ Error placing order: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def modify_order(self, client, order_data):
        """
        Modify an existing order
        
        INSERT YOUR JUPYTER NOTEBOOK ORDER MODIFICATION CODE HERE
        This method should implement the order modification logic from your notebook
        """
        try:
            response = client.modify_order(
                order_id=order_data.get('order_id'),
                price=float(order_data.get('price', 0)),
                quantity=int(order_data.get('quantity', 1)),
                disclosed_quantity=int(order_data.get('disclosed_quantity', 0)),
                trigger_price=float(order_data.get('trigger_price', 0)),
                validity=order_data.get('validity', 'DAY')
            )
            
            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Order modification failed'}
                
        except Exception as e:
            self.logger.error(f"Error modifying order: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def cancel_order(self, client, order_data):
        """
        Cancel an existing order
        
        INSERT YOUR JUPYTER NOTEBOOK ORDER CANCELLATION CODE HERE
        This method should implement the order cancellation logic from your notebook
        """
        try:
            response = client.cancel_order(
                order_id=order_data.get('order_id'),
                isVerify=order_data.get('isVerify', True)
            )
            
            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Order cancellation failed'}
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def get_quotes(self, client, quote_data):
        """Get live quotes for instruments based on Jupyter notebook implementation"""
        try:
            instrument_tokens = quote_data.get('instrument_tokens', [])
            quote_type = quote_data.get('quote_type', None)
            is_index = quote_data.get('is_index', False)
            
            self.logger.info(f"📊 Fetching quotes for {len(instrument_tokens)} instruments...")
            
            response = client.quotes(
                instrument_tokens=instrument_tokens,
                quote_type=quote_type,
                isIndex=is_index
            )
            
            if response and 'data' in response:
                self.logger.info("✅ Quotes retrieved successfully!")
                
                # Process quotes data
                processed_quotes = {}
                quotes_data = response['data']
                
                for token, quote_info in quotes_data.items():
                    processed_quotes[token] = {
                        'token': token,
                        'trading_symbol': quote_info.get('trdSym', ''),
                        'exchange_segment': quote_info.get('exSeg', ''),
                        'ltp': float(quote_info.get('ltp', 0)),
                        'last_traded_price': float(quote_info.get('ltp', 0)),
                        'open': float(quote_info.get('o', 0)),
                        'high': float(quote_info.get('h', 0)),
                        'low': float(quote_info.get('l', 0)),
                        'close': float(quote_info.get('c', 0)),
                        'volume': int(quote_info.get('v', 0)),
                        'change': float(quote_info.get('nc', 0)),
                        'change_percent': float(quote_info.get('cng', 0)),
                        'bid_price': float(quote_info.get('bp1', 0)),
                        'ask_price': float(quote_info.get('sp1', 0)),
                        'bid_quantity': int(quote_info.get('bq1', 0)),
                        'ask_quantity': int(quote_info.get('sq1', 0)),
                        'total_traded_value': float(quote_info.get('ttv', 0)),
                        'total_traded_quantity': int(quote_info.get('ttq', 0)),
                        'upper_circuit': float(quote_info.get('uc', 0)),
                        'lower_circuit': float(quote_info.get('lc', 0)),
                        'average_price': float(quote_info.get('ap', 0)),
                        'timestamp': quote_info.get('ft', ''),
                        'exchange_timestamp': quote_info.get('et', '')
                    }
                
                return {
                    'success': True, 
                    'data': processed_quotes,
                    'count': len(processed_quotes)
                }
            else:
                self.logger.error("❌ Failed to get quotes")
                return {'success': False, 'message': 'Failed to get quotes', 'response': response}
                
        except Exception as e:
            self.logger.error(f"❌ Error getting quotes: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_portfolio_summary(self, client):
        """Get comprehensive portfolio information"""
        try:
            self.logger.info("📊 Fetching portfolio summary...")
            
            # Get positions
            positions = client.positions()
            
            # Get holdings
            holdings = client.holdings()
            
            # Get limits
            limits = client.limits()
            
            self.logger.info("✅ Portfolio data fetched successfully!")
            
            # Display summary in console
            print("\n" + "="*60)
            print("📊 PORTFOLIO OVERVIEW")
            print("="*60)
            
            positions_count = 0
            holdings_count = 0
            
            if positions and 'data' in positions:
                positions_count = len(positions['data'])
                print(f"📈 Open Positions: {positions_count}")
            
            if holdings and 'data' in holdings:
                holdings_count = len(holdings['data'])
                print(f"🏦 Holdings: {holdings_count}")
                
            if limits:
                print(f"💰 Account Limits: Available")
            
            # Calculate summary statistics
            portfolio_summary = {
                'positions_count': positions_count,
                'holdings_count': holdings_count,
                'limits_available': limits is not None,
                'total_pnl': 0.0,
                'total_investment': 0.0,
                'day_change': 0.0,
                'available_margin': 0.0
            }
            
            # Calculate P&L from positions
            if positions and 'data' in positions:
                for position in positions['data']:
                    try:
                        pnl = float(position.get('pnl', 0) or 0)
                        portfolio_summary['total_pnl'] += pnl
                    except (ValueError, TypeError):
                        continue
            
            # Calculate investment value from holdings
            if holdings and 'data' in holdings:
                for holding in holdings['data']:
                    try:
                        quantity = float(holding.get('quantity', 0) or 0)
                        avg_price = float(holding.get('avgPrice', 0) or 0)
                        portfolio_summary['total_investment'] += quantity * avg_price
                    except (ValueError, TypeError):
                        continue
            
            # Get available margin from limits
            if limits and 'data' in limits:
                try:
                    portfolio_summary['available_margin'] = float(limits['data'].get('cash', 0) or 0)
                except (ValueError, TypeError):
                    portfolio_summary['available_margin'] = 0.0
            elif limits:
                try:
                    portfolio_summary['available_margin'] = float(limits.get('cash', 0) or 0)
                except (ValueError, TypeError):
                    portfolio_summary['available_margin'] = 0.0
            
            return {
                'success': True,
                'data': {
                    'positions': positions,
                    'holdings': holdings,
                    'limits': limits,
                    'summary': portfolio_summary
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch portfolio summary: {str(e)}")
            return {'success': False, 'message': str(e)}
