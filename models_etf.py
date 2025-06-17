from app import db
from datetime import datetime
import json


class ETFPosition(db.Model):
    """ETF Position model for trading signals"""
    __tablename__ = 'etf_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic position data
    etf_symbol = db.Column(db.String(50), nullable=False)  # ETF symbol
    trading_symbol = db.Column(db.String(100), nullable=False)  # Full trading symbol
    token = db.Column(db.String(50), nullable=False)  # Instrument token for API
    exchange = db.Column(db.String(10), nullable=False, default='NSE')
    
    # Position details
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    quantity = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Numeric(10, 2), nullable=False)  # EP
    target_price = db.Column(db.Numeric(10, 2), nullable=True)  # TP
    stop_loss = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Live market data (updated via WebSocket)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)  # CMP
    last_update_time = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    position_type = db.Column(db.String(10), default='LONG')  # LONG/SHORT
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('etf_positions', lazy=True))
    
    def __repr__(self):
        return f'<ETFPosition {self.etf_symbol}: {self.quantity}@{self.entry_price}>'
    
    @property
    def investment_amount(self):
        """Investment = Qty × EP"""
        return float(self.quantity * self.entry_price) if self.entry_price else 0
    
    @property
    def current_value(self):
        """Current Value = Qty × CMP"""
        return float(self.quantity * self.current_price) if self.current_price else 0
    
    @property
    def profit_loss(self):
        """P&L = (CMP - EP) × Qty"""
        if self.current_price and self.entry_price:
            return float((self.current_price - self.entry_price) * self.quantity)
        return 0
    
    @property
    def percentage_change(self):
        """%Change = ((CMP - EP) / EP) × 100"""
        if self.current_price and self.entry_price and self.entry_price > 0:
            return float(((self.current_price - self.entry_price) / self.entry_price) * 100)
        return 0
    
    @property
    def target_value_amount(self):
        """TVA = Qty × TP"""
        return float(self.quantity * self.target_price) if self.target_price else 0
    
    @property
    def target_profit_return(self):
        """TPR = TVA - Investment"""
        return self.target_value_amount - self.investment_amount
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'etf_symbol': self.etf_symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'quantity': self.quantity,
            'entry_price': float(self.entry_price) if self.entry_price else 0,
            'target_price': float(self.target_price) if self.target_price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'current_price': float(self.current_price) if self.current_price else 0,
            'position_type': self.position_type,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            # Calculated properties
            'investment_amount': self.investment_amount,
            'current_value': self.current_value,
            'profit_loss': self.profit_loss,
            'percentage_change': self.percentage_change,
            'target_value_amount': self.target_value_amount,
            'target_profit_return': self.target_profit_return
        return {
            'id': self.id,
            'etf_symbol': self.etf_symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'quantity': self.quantity,
            'entry_price': float(self.entry_price) if self.entry_price else 0,
            'current_price': float(self.current_price) if self.current_price else 0,
            'target_price': float(self.target_price) if self.target_price else 0,
            'stop_loss': float(self.stop_loss) if self.stop_loss else 0,
            'investment_amount': self.investment_amount,
            'current_value': self.current_value,
            'profit_loss': self.profit_loss,
            'percentage_change': self.percentage_change,
            'target_value_amount': self.target_value_amount,
            'target_profit_return': self.target_profit_return,
            'position_type': self.position_type,
            'notes': self.notes,
            'is_active': self.is_active,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ETFWatchlist(db.Model):
    """ETF Watchlist for instruments to track"""
    __tablename__ = 'etf_watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    symbol = db.Column(db.String(50), nullable=False)
    trading_symbol = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(50), nullable=False)
    exchange = db.Column(db.String(10), nullable=False, default='NSE')
    
    # Live data
    ltp = db.Column(db.Numeric(10, 2), nullable=True)
    change = db.Column(db.Numeric(10, 2), nullable=True)
    change_percent = db.Column(db.Numeric(5, 2), nullable=True)
    volume = db.Column(db.BigInteger, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_update_time = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('etf_watchlist', lazy=True))
    
    def __repr__(self):
        return f'<ETFWatchlist {self.symbol}@{self.ltp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'ltp': float(self.ltp) if self.ltp else 0,
            'change': float(self.change) if self.change else 0,
            'change_percent': float(self.change_percent) if self.change_percent else 0,
            'volume': self.volume or 0,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None
        }