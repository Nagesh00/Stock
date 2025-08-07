"""
Market Data Models

Data structures for financial market data with proper validation
and serialization support for the trading system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
import json


@dataclass
class MarketTick:
    """Single market data tick/quote"""
    symbol: str
    price: float
    volume: int
    bid: float
    ask: float
    timestamp: datetime
    source: str
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_size: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'bid': self.bid,
            'ask': self.ask,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'last_size': self.last_size,
            'high': self.high,
            'low': self.low,
            'open_price': self.open_price,
            'close_price': self.close_price
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketTick':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class OHLCV:
    """OHLCV (Open, High, Low, Close, Volume) bar data"""
    symbol: str
    open_price: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    timeframe: str  # '1m', '5m', '1h', '1d', etc.
    source: str
    vwap: Optional[float] = None  # Volume Weighted Average Price
    trades_count: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'open': self.open_price,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'timeframe': self.timeframe,
            'source': self.source,
            'vwap': self.vwap,
            'trades_count': self.trades_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OHLCV':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['open_price'] = data.pop('open')
        return cls(**data)


@dataclass
class OrderBookLevel:
    """Single level in order book"""
    price: float
    size: int
    orders: Optional[int] = None


@dataclass
class OrderBook:
    """Order book with multiple levels"""
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime
    source: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'bids': [{'price': b.price, 'size': b.size, 'orders': b.orders} for b in self.bids],
            'asks': [{'price': a.price, 'size': a.size, 'orders': a.orders} for a in self.asks],
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }
    
    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        """Get best bid (highest price)"""
        return max(self.bids, key=lambda x: x.price) if self.bids else None
    
    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        """Get best ask (lowest price)"""
        return min(self.asks, key=lambda x: x.price) if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Get bid-ask spread"""
        best_bid = self.best_bid
        best_ask = self.best_ask
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None


@dataclass
class Trade:
    """Individual trade/transaction"""
    symbol: str
    price: float
    size: int
    side: str  # 'buy' or 'sell'
    timestamp: datetime
    trade_id: Optional[str] = None
    source: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'size': self.size,
            'side': self.side,
            'timestamp': self.timestamp.isoformat(),
            'trade_id': self.trade_id,
            'source': self.source
        }


@dataclass
class NewsItem:
    """Financial news item"""
    title: str
    content: str
    source: str
    symbols: List[str]
    timestamp: datetime
    sentiment_score: float = 0.0  # -1 to 1, where -1 is very negative, 1 is very positive
    url: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None  # 'earnings', 'merger', 'regulation', etc.
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'symbols': self.symbols,
            'timestamp': self.timestamp.isoformat(),
            'sentiment_score': self.sentiment_score,
            'url': self.url,
            'author': self.author,
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NewsItem':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class TechnicalIndicator:
    """Technical indicator value"""
    symbol: str
    indicator_name: str
    value: float
    timestamp: datetime
    timeframe: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'indicator_name': self.indicator_name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'timeframe': self.timeframe,
            'parameters': self.parameters
        }


@dataclass
class Signal:
    """Trading signal generated by AI models"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0 to 1
    price_target: Optional[float]
    stop_loss: Optional[float]
    timestamp: datetime
    model_name: str
    features: Dict[str, float] = field(default_factory=dict)
    reasoning: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'price_target': self.price_target,
            'stop_loss': self.stop_loss,
            'timestamp': self.timestamp.isoformat(),
            'model_name': self.model_name,
            'features': self.features,
            'reasoning': self.reasoning
        }


@dataclass
class Position:
    """Trading position"""
    symbol: str
    quantity: int  # Positive for long, negative for short
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return abs(self.quantity) * self.current_price
    
    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'timestamp': self.timestamp.isoformat(),
            'market_value': self.market_value,
            'is_long': self.is_long,
            'is_short': self.is_short
        }


@dataclass
class Order:
    """Trading order"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    order_type: str  # 'market', 'limit', 'stop', 'stop_limit'
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = 'pending'  # 'pending', 'filled', 'cancelled', 'rejected'
    filled_quantity: int = 0
    avg_fill_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    time_in_force: str = 'DAY'  # 'DAY', 'GTC', 'IOC', 'FOK'
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.filled_quantity == self.quantity
    
    @property
    def remaining_quantity(self) -> int:
        """Get remaining quantity to be filled"""
        return self.quantity - self.filled_quantity
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'order_type': self.order_type,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'avg_fill_price': self.avg_fill_price,
            'timestamp': self.timestamp.isoformat(),
            'time_in_force': self.time_in_force,
            'is_filled': self.is_filled,
            'remaining_quantity': self.remaining_quantity
        }
