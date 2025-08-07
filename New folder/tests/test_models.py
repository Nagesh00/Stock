"""
Test market data models
"""
import pytest
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models.market_data import MarketTick, OHLCV


class TestMarketData:
    def test_market_tick_creation(self):
        """Test MarketTick model creation and validation"""
        tick = MarketTick(
            symbol="RELIANCE",
            timestamp=datetime.now(),
            price=2500.50,
            volume=1000,
            bid=2500.25,
            ask=2500.75,
            source="test"
        )
        assert tick.symbol == "RELIANCE"
        assert tick.price == 2500.50
        assert tick.volume == 1000
    
    def test_ohlcv_creation(self):
        """Test OHLCV model creation"""
        ohlcv = OHLCV(
            symbol="RELIANCE",
            timestamp=datetime.now(),
            open_price=2500.00,
            high=2550.00,
            low=2490.00,
            close=2530.00,
            volume=50000,
            timeframe="1d",
            source="test"
        )
        assert ohlcv.symbol == "RELIANCE"
        assert ohlcv.high == 2550.00
        assert ohlcv.low == 2490.00
