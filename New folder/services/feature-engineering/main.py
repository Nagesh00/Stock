"""
Feature Engineering Service

Responsible for calculating technical indicators, sentiment scores,
and other features required by AI models for signal generation.

Features:
- Real-time technical indicator calculation
- Sentiment analysis using FinBERT
- Feature normalization and scaling
- Streaming feature computation with state management
- Integration with time-series database
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import time

try:
    import talib  # type: ignore
    TALIB_AVAILABLE = True
except ImportError:
    print("Warning: TA-Lib not available. Using built-in indicators.")
    TALIB_AVAILABLE = False

# Import our built-in technical indicators
from shared.utils.technical_indicators import TechnicalIndicators
from kafka import KafkaConsumer
from transformers import BertTokenizer, BertForSequenceClassification
import torch
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from shared.config import Config
from shared.models.market_data import MarketTick, NewsItem, TechnicalIndicator
from shared.kafka.producer import KafkaDataProducer
from shared.utils.database import DatabaseManager
from shared.utils.logging import setup_logging


# Metrics
FEATURES_CALCULATED = Counter('features_calculated_total', 
                             'Total features calculated', ['symbol', 'indicator'])
PROCESSING_LATENCY = Histogram('feature_processing_latency_seconds',
                              'Feature processing latency', ['indicator_type'])
CACHE_SIZE = Gauge('feature_cache_size', 'Size of feature cache')
SENTIMENT_PROCESSED = Counter('sentiment_analysis_total',
                             'Total sentiment analyses performed')


@dataclass
class FeatureState:
    """Maintains state for streaming feature calculation"""
    symbol: str
    prices: List[float]
    volumes: List[int]
    timestamps: List[datetime]
    max_length: int = 200  # Keep last 200 data points
    
    def add_tick(self, tick: MarketTick):
        """Add new market tick to state"""
        self.prices.append(tick.price)
        self.volumes.append(tick.volume)
        self.timestamps.append(tick.timestamp)
        
        # Maintain max length
        if len(self.prices) > self.max_length:
            self.prices.pop(0)
            self.volumes.pop(0)
            self.timestamps.pop(0)
    
    @property
    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for calculations"""
        return len(self.prices) >= 50  # Need at least 50 points
    
    def get_price_series(self, length: Optional[int] = None) -> np.ndarray:
        """Get price series as numpy array"""
        if length and len(self.prices) >= length:
            return np.array(self.prices[-length:])
        return np.array(self.prices)
    
    def get_volume_series(self, length: Optional[int] = None) -> np.ndarray:
        """Get volume series as numpy array"""
        if length and len(self.volumes) >= length:
            return np.array(self.volumes[-length:])
        return np.array(self.volumes)


class TechnicalIndicatorCalculator:
    """Calculate technical indicators using TA-Lib"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def calculate_sma(self, prices: np.ndarray, period: int = 20) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        
        try:
            if TALIB_AVAILABLE:
                sma = talib.SMA(prices, timeperiod=period)
                return float(sma[-1]) if not np.isnan(sma[-1]) else None
            else:
                # Use built-in calculation
                prices_series = pd.Series(prices)
                sma = TechnicalIndicators.sma(prices_series, period)
                return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
        except Exception as e:
            self.logger.error("SMA calculation failed", period=period, error=str(e))
            return None
    
    def calculate_ema(self, prices: np.ndarray, period: int = 12) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        try:
            if TALIB_AVAILABLE:
                ema = talib.EMA(prices, timeperiod=period)
                return float(ema[-1]) if not np.isnan(ema[-1]) else None
            else:
                # Use built-in calculation
                prices_series = pd.Series(prices)
                ema = TechnicalIndicators.ema(prices_series, period)
                return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else None
        except Exception as e:
            self.logger.error("EMA calculation failed", period=period, error=str(e))
            return None
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        try:
            if TALIB_AVAILABLE:
                rsi = talib.RSI(prices, timeperiod=period)
                return float(rsi[-1]) if not np.isnan(rsi[-1]) else None
            else:
                # Use built-in calculation
                prices_series = pd.Series(prices)
                rsi = TechnicalIndicators.rsi(prices_series, period)
                return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception as e:
            self.logger.error("RSI calculation failed", period=period, error=str(e))
            return None
    
    def calculate_macd(self, prices: np.ndarray) -> Dict[str, Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < 34:  # Need at least 34 periods for MACD
            return {"macd": None, "signal": None, "histogram": None}
        
        try:
            if TALIB_AVAILABLE:
                macd, signal, histogram = talib.MACD(prices, 
                                                   fastperiod=12, 
                                                   slowperiod=26, 
                                                   signalperiod=9)
                
                return {
                    "macd": float(macd[-1]) if not np.isnan(macd[-1]) else None,
                    "signal": float(signal[-1]) if not np.isnan(signal[-1]) else None,
                    "histogram": float(histogram[-1]) if not np.isnan(histogram[-1]) else None
                }
            else:
                # Use built-in calculation
                prices_series = pd.Series(prices)
                macd_data = TechnicalIndicators.macd(prices_series)
                
                return {
                    "macd": float(macd_data['macd'].iloc[-1]) if not pd.isna(macd_data['macd'].iloc[-1]) else None,
                    "signal": float(macd_data['signal'].iloc[-1]) if not pd.isna(macd_data['signal'].iloc[-1]) else None,
                    "histogram": float(macd_data['histogram'].iloc[-1]) if not pd.isna(macd_data['histogram'].iloc[-1]) else None
                }
        except Exception as e:
            self.logger.error("MACD calculation failed", error=str(e))
            return {"macd": None, "signal": None, "histogram": None}
    
    def calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, 
                                 std_dev: int = 2) -> Dict[str, Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        
        try:
            upper, middle, lower = talib.BBANDS(prices, 
                                              timeperiod=period, 
                                              nbdevup=std_dev, 
                                              nbdevdn=std_dev)
            
            return {
                "upper": float(upper[-1]) if not np.isnan(upper[-1]) else None,
                "middle": float(middle[-1]) if not np.isnan(middle[-1]) else None,
                "lower": float(lower[-1]) if not np.isnan(lower[-1]) else None
            }
        except Exception as e:
            self.logger.error("Bollinger Bands calculation failed", error=str(e))
            return {"upper": None, "middle": None, "lower": None}
    
    def calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                     period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(close) < period + 1:
            return None
        
        try:
            atr = talib.ATR(high, low, close, timeperiod=period)
            return float(atr[-1]) if not np.isnan(atr[-1]) else None
        except Exception as e:
            self.logger.error("ATR calculation failed", period=period, error=str(e))
            return None
    
    def calculate_all_indicators(self, state: FeatureState) -> Dict[str, Any]:
        """Calculate all technical indicators for a symbol"""
        if not state.has_sufficient_data:
            return {}
        
        prices = state.get_price_series()
        indicators = {}
        
        # Moving averages
        indicators['sma_20'] = self.calculate_sma(prices, 20)
        indicators['sma_50'] = self.calculate_sma(prices, 50)
        indicators['ema_12'] = self.calculate_ema(prices, 12)
        indicators['ema_26'] = self.calculate_ema(prices, 26)
        
        # Momentum indicators
        indicators['rsi'] = self.calculate_rsi(prices)
        macd_data = self.calculate_macd(prices)
        indicators.update(macd_data)
        
        # Volatility indicators
        bb_data = self.calculate_bollinger_bands(prices)
        indicators.update({f"bb_{k}": v for k, v in bb_data.items()})
        
        # For ATR, we need high/low data - using price as approximation
        high = prices * 1.01  # Approximate high as price + 1%
        low = prices * 0.99   # Approximate low as price - 1%
        indicators['atr'] = self.calculate_atr(high, low, prices)
        
        return {k: v for k, v in indicators.items() if v is not None}


class SentimentAnalyzer:
    """Analyze sentiment using FinBERT model"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.logger = structlog.get_logger(__name__)
        self.model_name = model_name
        
        try:
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            
            self.logger.info("FinBERT model loaded successfully", model=model_name)
        except Exception as e:
            self.logger.error("Failed to load FinBERT model", error=str(e))
            self.tokenizer = None
            self.model = None
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of financial text
        
        Returns:
            Dict with sentiment scores: positive, negative, neutral
        """
        if not self.model or not self.tokenizer:
            self.logger.warning("Model not available, returning neutral sentiment")
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "score": 0.0}
        
        try:
            # Tokenize input
            inputs = self.tokenizer(text, 
                                  return_tensors="pt", 
                                  truncation=True, 
                                  padding=True, 
                                  max_length=512)
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Extract probabilities
            probs = predictions[0].tolist()
            
            # FinBERT classes: negative, neutral, positive
            sentiment_scores = {
                "negative": probs[0],
                "neutral": probs[1], 
                "positive": probs[2]
            }
            
            # Calculate overall sentiment score (-1 to 1)
            sentiment_score = probs[2] - probs[0]  # positive - negative
            sentiment_scores["score"] = sentiment_score
            
            SENTIMENT_PROCESSED.inc()
            
            return sentiment_scores
            
        except Exception as e:
            self.logger.error("Sentiment analysis failed", error=str(e))
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "score": 0.0}


class FeatureEngineeringService:
    """Main feature engineering service"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # Initialize components
        self.kafka_producer = KafkaDataProducer(config.kafka_bootstrap_servers)
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.sentiment_analyzer = SentimentAnalyzer(config.ml.sentiment_model_path)
        self.db_manager = DatabaseManager(config.database_url)
        
        # State management for streaming calculations
        self.feature_states: Dict[str, FeatureState] = {}
        
        # Kafka consumers
        self.market_data_consumer = None
        self.news_consumer = None
        
        self.running = False
    
    async def start(self):
        """Start the feature engineering service"""
        self.running = True
        self.logger.info("Starting feature engineering service")
        
        # Start metrics server
        start_http_server(8001)
        
        # Initialize Kafka consumers
        self._initialize_consumers()
        
        # Start processing tasks
        tasks = [
            asyncio.create_task(self._process_market_data()),
            asyncio.create_task(self._process_news_data()),
            asyncio.create_task(self._periodic_feature_calculation())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the service"""
        self.running = False
        self.logger.info("Stopping feature engineering service")
        
        if self.market_data_consumer:
            self.market_data_consumer.close()
        if self.news_consumer:
            self.news_consumer.close()
        
        self.kafka_producer.close()
    
    def _initialize_consumers(self):
        """Initialize Kafka consumers"""
        consumer_config = {
            'bootstrap_servers': self.config.kafka_bootstrap_servers,
            'group_id': 'feature-engineering',
            'auto_offset_reset': 'latest',
            'enable_auto_commit': True,
            'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
        }
        
        # Market data consumer
        self.market_data_consumer = KafkaConsumer(
            'market_data_raw', **consumer_config
        )
        
        # News consumer
        self.news_consumer = KafkaConsumer(
            'financial_news', **consumer_config
        )
    
    async def _process_market_data(self):
        """Process incoming market data and calculate features"""
        while self.running:
            try:
                # Poll for new messages
                message_batch = self.market_data_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._handle_market_tick(message.value)
                
                await asyncio.sleep(0.1)  # Prevent tight loop
                
            except Exception as e:
                self.logger.error("Market data processing error", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_news_data(self):
        """Process incoming news data for sentiment analysis"""
        while self.running:
            try:
                # Poll for new messages
                message_batch = self.news_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._handle_news_item(message.value)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error("News processing error", error=str(e))
                await asyncio.sleep(1)
    
    async def _handle_market_tick(self, tick_data: dict):
        """Handle individual market tick"""
        try:
            start_time = time.time()
            
            # Convert to MarketTick object
            tick = MarketTick.from_dict(tick_data)
            symbol = tick.symbol
            
            # Initialize or update feature state
            if symbol not in self.feature_states:
                self.feature_states[symbol] = FeatureState(symbol, [], [], [])
            
            state = self.feature_states[symbol]
            state.add_tick(tick)
            
            # Calculate features if we have sufficient data
            if state.has_sufficient_data:
                features = self.technical_calculator.calculate_all_indicators(state)
                
                if features:
                    # Add metadata
                    feature_data = {
                        'symbol': symbol,
                        'timestamp': tick.timestamp.isoformat(),
                        'price': tick.price,
                        'features': features
                    }
                    
                    # Send to Kafka
                    await self.kafka_producer.send_async(
                        'technical_features', feature_data
                    )
                    
                    # Record metrics
                    for indicator_name in features.keys():
                        FEATURES_CALCULATED.labels(
                            symbol=symbol, indicator=indicator_name
                        ).inc()
            
            # Record processing latency
            latency = time.time() - start_time
            PROCESSING_LATENCY.labels(indicator_type='technical').observe(latency)
            
            # Update cache size metric
            CACHE_SIZE.set(len(self.feature_states))
            
        except Exception as e:
            self.logger.error("Market tick processing failed", error=str(e))
    
    async def _handle_news_item(self, news_data: dict):
        """Handle news item for sentiment analysis"""
        try:
            start_time = time.time()
            
            # Convert to NewsItem object
            news_item = NewsItem.from_dict(news_data)
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(
                f"{news_item.title} {news_item.content}"
            )
            
            # Create sentiment feature
            sentiment_data = {
                'symbols': news_item.symbols,
                'timestamp': news_item.timestamp.isoformat(),
                'sentiment': sentiment,
                'source': news_item.source,
                'title': news_item.title
            }
            
            # Send to Kafka
            await self.kafka_producer.send_async(
                'sentiment_scores', sentiment_data
            )
            
            # Record processing latency
            latency = time.time() - start_time
            PROCESSING_LATENCY.labels(indicator_type='sentiment').observe(latency)
            
        except Exception as e:
            self.logger.error("News processing failed", error=str(e))
    
    async def _periodic_feature_calculation(self):
        """Periodically recalculate features and clean up old data"""
        while self.running:
            try:
                # Clean up old states
                current_time = datetime.now()
                symbols_to_remove = []
                
                for symbol, state in self.feature_states.items():
                    if (state.timestamps and 
                        current_time - state.timestamps[-1] > timedelta(hours=1)):
                        symbols_to_remove.append(symbol)
                
                for symbol in symbols_to_remove:
                    del self.feature_states[symbol]
                    self.logger.debug("Removed stale feature state", symbol=symbol)
                
                # Wait before next cleanup
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error("Periodic cleanup failed", error=str(e))
                await asyncio.sleep(60)


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = structlog.get_logger(__name__)
    
    # Load configuration
    config = Config()
    
    # Create and start service
    service = FeatureEngineeringService(config)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
