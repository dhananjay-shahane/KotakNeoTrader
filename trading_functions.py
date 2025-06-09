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
        """
        Place a new order
        
        INSERT YOUR JUPYTER NOTEBOOK ORDER PLACEMENT CODE HERE
        This method should implement the order placement logic from your notebook
        """
        try:
            # Example order placement (customize based on your notebook code)
            response = client.place_order(
                exchange_segment=order_data.get('exchange_segment', 'nse_cm'),
                product=order_data.get('product', 'CNC'),
                price=order_data.get('price', '0'),
                order_type=order_data.get('order_type', 'MARKET'),
                quantity=int(order_data.get('quantity', 1)),
                validity=order_data.get('validity', 'DAY'),
                trading_symbol=order_data.get('trading_symbol', ''),
                transaction_type=order_data.get('transaction_type', 'BUY'),
                amo=order_data.get('amo', 'NO'),
                disclosed_quantity=order_data.get('disclosed_quantity', '0'),
                market_protection=order_data.get('market_protection', '0'),
                pf=order_data.get('pf', 'N'),
                trigger_price=order_data.get('trigger_price', '0'),
                tag=order_data.get('tag', None)
            )
            
            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Order placement failed'}
                
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
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
        """
        Get live quotes for instruments
        
        INSERT YOUR JUPYTER NOTEBOOK QUOTES FETCHING CODE HERE
        This method should implement the quotes fetching logic from your notebook
        """
        try:
            instrument_tokens = quote_data.get('instrument_tokens', [])
            quote_type = quote_data.get('quote_type', None)
            is_index = quote_data.get('is_index', False)
            
            response = client.quotes(
                instrument_tokens=instrument_tokens,
                quote_type=quote_type,
                isIndex=is_index
            )
            
            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Failed to get quotes'}
                
        except Exception as e:
            self.logger.error(f"Error getting quotes: {str(e)}")
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
            
            # Calculate summary statistics
            portfolio_summary = {
                'positions_count': len(positions['data']) if positions and 'data' in positions else 0,
                'holdings_count': len(holdings['data']) if holdings and 'data' in holdings else 0,
                'limits_available': limits is not None,
                'total_pnl': 0.0,
                'total_investment': 0.0,
                'day_change': 0.0
            }
            
            # Calculate P&L from positions
            if positions and 'data' in positions:
                for position in positions['data']:
                    pnl = float(position.get('pnl', 0) or 0)
                    portfolio_summary['total_pnl'] += pnl
            
            # Calculate investment value from holdings
            if holdings and 'data' in holdings:
                for holding in holdings['data']:
                    try:
                        quantity = float(holding.get('quantity', 0) or 0)
                        avg_price = float(holding.get('avgPrice', 0) or 0)
                        portfolio_summary['total_investment'] += quantity * avg_price
                    except (ValueError, TypeError):
                        continue
            
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
