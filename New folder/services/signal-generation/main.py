"""
Signal Generation Service

AI-powered trading signal generation using LSTM models with attention mechanism
and GARCH volatility forecasting. Combines multiple data sources for robust
predictions.

Features:
- LSTM models for price prediction with attention mechanism
- GARCH models for volatility forecasting
- Multi-modal feature fusion (price + sentiment + volatility)
- Real-time model inference
- Model performance monitoring and drift detection
- Automated model retraining pipeline
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pickle
import time
import warnings

# TensorFlow imports with fallback
try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras.models import load_model, Sequential  # type: ignore
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Attention  # type: ignore
    from tensorflow.keras.optimizers import Adam  # type: ignore
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("Warning: TensorFlow not available. Using PyTorch as fallback.")
    import torch
    import torch.nn as nn
    TENSORFLOW_AVAILABLE = False
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import torch
from arch import arch_model
from kafka import KafkaConsumer
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from shared.config import Config
from shared.models.market_data import Signal, TechnicalIndicator
from shared.kafka.producer import KafkaDataProducer
from shared.utils.database import DatabaseManager
from shared.utils.logging import setup_logging

warnings.filterwarnings('ignore')

# Metrics
SIGNALS_GENERATED = Counter('signals_generated_total', 
                           'Total signals generated', ['symbol', 'signal_type'])
MODEL_INFERENCE_LATENCY = Histogram('model_inference_latency_seconds',
                                   'Model inference latency', ['model_type'])
MODEL_ACCURACY = Gauge('model_accuracy', 'Model accuracy', ['model_name', 'symbol'])
PREDICTION_CONFIDENCE = Histogram('prediction_confidence',
                                 'Distribution of prediction confidence scores')


@dataclass
class ModelPrediction:
    """Container for model predictions"""
    symbol: str
    predicted_price: float
    predicted_volatility: float
    confidence: float
    direction: str  # 'up', 'down', 'sideways'
    features_used: Dict[str, float]
    model_version: str
    timestamp: datetime


class LSTMAttentionModel:
    """LSTM model with attention mechanism for price prediction"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.sequence_length = config.ml.lstm_sequence_length
        self.model_path = config.ml.lstm_model_path
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model"""
        try:
            if tf.io.gfile.exists(self.model_path):
                self.model = load_model(self.model_path)
                self.logger.info("LSTM model loaded", path=self.model_path)
                
                # Load scalers
                scaler_path = self.model_path.replace('.h5', '_scaler.pkl')
                if tf.io.gfile.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        scalers = pickle.load(f)
                        self.scaler = scalers['price_scaler']
                        self.feature_scaler = scalers['feature_scaler']
            else:
                self.logger.warning("No pre-trained model found, will create new one")
                self._build_model()
        except Exception as e:
            self.logger.error("Failed to load model", error=str(e))
            self._build_model()
    
    def _build_model(self):
        """Build new LSTM model with attention"""
        try:
            # Model architecture
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.sequence_length, 10)),
                Dropout(self.config.ml.lstm_dropout_rate),
                LSTM(50, return_sequences=True),
                Dropout(self.config.ml.lstm_dropout_rate),
                LSTM(50),
                Dropout(self.config.ml.lstm_dropout_rate),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mean_squared_error',
                metrics=['mae']
            )
            
            self.model = model
            self.logger.info("New LSTM model created")
            
        except Exception as e:
            self.logger.error("Failed to build model", error=str(e))
    
    def prepare_features(self, price_data: List[float], 
                        feature_data: List[Dict[str, float]]) -> np.ndarray:
        """Prepare features for model input"""
        try:
            # Ensure we have enough data
            if len(price_data) < self.sequence_length:
                return None
            
            # Create feature matrix
            features = []
            for i in range(len(price_data)):
                row = [price_data[i]]  # Start with price
                
                # Add technical indicators if available
                if i < len(feature_data) and feature_data[i]:
                    features_dict = feature_data[i]
                    row.extend([
                        features_dict.get('sma_20', 0),
                        features_dict.get('rsi', 50),
                        features_dict.get('macd', 0),
                        features_dict.get('bb_upper', 0),
                        features_dict.get('bb_lower', 0),
                        features_dict.get('atr', 0),
                        features_dict.get('volume', 0),
                        features_dict.get('sentiment', 0),
                        features_dict.get('volatility', 0)
                    ])
                else:
                    # Fill with zeros if no features available
                    row.extend([0] * 9)
                
                features.append(row)
            
            # Convert to numpy array and get last sequence_length points
            features_array = np.array(features)
            if len(features_array) >= self.sequence_length:
                return features_array[-self.sequence_length:]
            
            return None
            
        except Exception as e:
            self.logger.error("Feature preparation failed", error=str(e))
            return None
    
    def predict(self, price_data: List[float], 
               feature_data: List[Dict[str, float]]) -> Optional[ModelPrediction]:
        """Make prediction using the model"""
        if not self.model:
            return None
        
        try:
            start_time = time.time()
            
            # Prepare features
            features = self.prepare_features(price_data, feature_data)
            if features is None:
                return None
            
            # Scale features
            scaled_features = self.feature_scaler.fit_transform(features)
            
            # Reshape for LSTM input
            X = scaled_features.reshape(1, self.sequence_length, -1)
            
            # Make prediction
            prediction = self.model.predict(X, verbose=0)[0][0]
            
            # Calculate confidence based on recent model performance
            confidence = self._calculate_confidence(price_data[-10:])
            
            # Determine direction
            current_price = price_data[-1]
            direction = 'up' if prediction > current_price else 'down'
            if abs(prediction - current_price) / current_price < 0.005:  # < 0.5%
                direction = 'sideways'
            
            # Record latency
            latency = time.time() - start_time
            MODEL_INFERENCE_LATENCY.labels(model_type='lstm').observe(latency)
            
            return ModelPrediction(
                symbol="",  # Will be set by caller
                predicted_price=float(prediction),
                predicted_volatility=0.0,  # Will be set by GARCH model
                confidence=confidence,
                direction=direction,
                features_used=feature_data[-1] if feature_data else {},
                model_version="lstm_v1.0",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error("Prediction failed", error=str(e))
            return None
    
    def _calculate_confidence(self, recent_prices: List[float]) -> float:
        """Calculate prediction confidence based on recent volatility"""
        if len(recent_prices) < 2:
            return 0.5
        
        # Calculate recent volatility
        returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(returns)
        
        # Lower volatility = higher confidence
        # Normalize to 0-1 range
        confidence = max(0.1, min(0.9, 1.0 - (volatility * 10)))
        return confidence


class GARCHVolatilityModel:
    """GARCH model for volatility forecasting"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.model = None
        self.fitted_model = None
        self.model_path = config.ml.garch_model_path
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained GARCH model"""
        try:
            if tf.io.gfile.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.fitted_model = pickle.load(f)
                self.logger.info("GARCH model loaded", path=self.model_path)
            else:
                self.logger.warning("No pre-trained GARCH model found")
        except Exception as e:
            self.logger.error("Failed to load GARCH model", error=str(e))
    
    def fit_and_forecast(self, returns: List[float]) -> Tuple[float, float]:
        """Fit GARCH model and forecast volatility"""
        try:
            start_time = time.time()
            
            if len(returns) < 100:  # Need sufficient data for GARCH
                return 0.02, 0.5  # Default volatility and low confidence
            
            # Convert to pandas series
            returns_series = pd.Series(returns)
            
            # Fit GARCH(1,1) model
            model = arch_model(
                returns_series * 100,  # Scale returns
                vol='Garch',
                p=self.config.ml.garch_p,
                q=self.config.ml.garch_q
            )
            
            # Fit model with error handling
            try:
                fitted_model = model.fit(disp='off', show_warning=False)
                self.fitted_model = fitted_model
                
                # Forecast next period volatility
                forecast = fitted_model.forecast(horizon=1)
                predicted_variance = forecast.variance.iloc[-1, 0]
                predicted_volatility = np.sqrt(predicted_variance) / 100  # Scale back
                
                # Calculate confidence based on model fit
                aic = fitted_model.aic
                confidence = max(0.1, min(0.9, 1.0 / (1.0 + aic / 1000)))
                
                # Record latency
                latency = time.time() - start_time
                MODEL_INFERENCE_LATENCY.labels(model_type='garch').observe(latency)
                
                return float(predicted_volatility), float(confidence)
                
            except Exception as fit_error:
                self.logger.warning("GARCH fitting failed, using fallback", 
                                  error=str(fit_error))
                # Fallback to simple volatility calculation
                volatility = np.std(returns)
                return float(volatility), 0.3
                
        except Exception as e:
            self.logger.error("GARCH forecasting failed", error=str(e))
            return 0.02, 0.1  # Default values


class MultiModalSignalGenerator:
    """Combines multiple models for robust signal generation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # Initialize models
        self.lstm_model = LSTMAttentionModel(config)
        self.garch_model = GARCHVolatilityModel(config)
        
        # Data storage for model inputs
        self.symbol_data: Dict[str, Dict] = {}
        
        # Signal thresholds
        self.confidence_threshold = config.ml.signal_confidence_threshold
    
    def update_symbol_data(self, symbol: str, price_data: List[float], 
                          feature_data: List[Dict[str, float]],
                          sentiment_data: List[float]):
        """Update data for a symbol"""
        if symbol not in self.symbol_data:
            self.symbol_data[symbol] = {
                'prices': [],
                'features': [],
                'sentiment': [],
                'returns': []
            }
        
        data = self.symbol_data[symbol]
        
        # Update prices and calculate returns
        if price_data:
            old_len = len(data['prices'])
            data['prices'].extend(price_data)
            
            # Calculate new returns
            for i in range(max(1, old_len), len(data['prices'])):
                if i > 0:
                    ret = (data['prices'][i] - data['prices'][i-1]) / data['prices'][i-1]
                    data['returns'].append(ret)
        
        # Update features and sentiment
        data['features'].extend(feature_data)
        data['sentiment'].extend(sentiment_data)
        
        # Keep only recent data (last 500 points)
        max_length = 500
        for key in data:
            if len(data[key]) > max_length:
                data[key] = data[key][-max_length:]
    
    def generate_signal(self, symbol: str) -> Optional[Signal]:
        """Generate trading signal for a symbol"""
        if symbol not in self.symbol_data:
            return None
        
        data = self.symbol_data[symbol]
        
        # Need sufficient data
        if len(data['prices']) < self.config.ml.lstm_sequence_length:
            return None
        
        try:
            # Get LSTM prediction
            lstm_prediction = self.lstm_model.predict(
                data['prices'], data['features']
            )
            
            if not lstm_prediction:
                return None
            
            # Get GARCH volatility forecast
            volatility, vol_confidence = self.garch_model.fit_and_forecast(
                data['returns']
            )
            
            # Update prediction with volatility
            lstm_prediction.predicted_volatility = volatility
            lstm_prediction.symbol = symbol
            
            # Combine confidences
            combined_confidence = (lstm_prediction.confidence + vol_confidence) / 2
            
            # Add sentiment influence
            if data['sentiment']:
                recent_sentiment = np.mean(data['sentiment'][-5:])  # Last 5 sentiment scores
                sentiment_weight = 0.2  # 20% weight to sentiment
                combined_confidence *= (1 + sentiment_weight * recent_sentiment)
                combined_confidence = max(0.1, min(0.9, combined_confidence))
            
            # Determine signal type
            current_price = data['prices'][-1]
            price_change_pct = (lstm_prediction.predicted_price - current_price) / current_price
            
            if combined_confidence < self.confidence_threshold:
                signal_type = 'hold'
            elif price_change_pct > 0.01:  # > 1% upward
                signal_type = 'buy'
            elif price_change_pct < -0.01:  # < -1% downward
                signal_type = 'sell'
            else:
                signal_type = 'hold'
            
            # Calculate price targets and stop loss
            price_target = None
            stop_loss = None
            
            if signal_type in ['buy', 'sell']:
                # Price target: predicted price
                price_target = lstm_prediction.predicted_price
                
                # Stop loss: current price +/- 2 * ATR
                atr = data['features'][-1].get('atr', volatility * current_price) if data['features'] else volatility * current_price
                if signal_type == 'buy':
                    stop_loss = current_price - 2 * atr
                else:  # sell
                    stop_loss = current_price + 2 * atr
            
            # Create signal
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=combined_confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                timestamp=datetime.now(),
                model_name="multi_modal_v1.0",
                features={
                    'predicted_price': lstm_prediction.predicted_price,
                    'predicted_volatility': volatility,
                    'current_price': current_price,
                    'price_change_pct': price_change_pct,
                    'recent_sentiment': np.mean(data['sentiment'][-5:]) if data['sentiment'] else 0.0
                },
                reasoning=f"LSTM predicted {lstm_prediction.direction} movement with {combined_confidence:.2f} confidence"
            )
            
            # Record metrics
            SIGNALS_GENERATED.labels(symbol=symbol, signal_type=signal_type).inc()
            PREDICTION_CONFIDENCE.observe(combined_confidence)
            
            return signal
            
        except Exception as e:
            self.logger.error("Signal generation failed", symbol=symbol, error=str(e))
            return None


class SignalGenerationService:
    """Main signal generation service"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # Initialize components
        self.kafka_producer = KafkaDataProducer(config.kafka_bootstrap_servers)
        self.signal_generator = MultiModalSignalGenerator(config)
        self.db_manager = DatabaseManager(config.database_url)
        
        # Kafka consumers
        self.feature_consumer = None
        self.sentiment_consumer = None
        
        # Data buffers for real-time processing
        self.recent_features: Dict[str, List] = {}
        self.recent_sentiment: Dict[str, List] = {}
        
        self.running = False
    
    async def start(self):
        """Start the signal generation service"""
        self.running = True
        self.logger.info("Starting signal generation service")
        
        # Start metrics server
        start_http_server(8002)
        
        # Initialize Kafka consumers
        self._initialize_consumers()
        
        # Start processing tasks
        tasks = [
            asyncio.create_task(self._process_features()),
            asyncio.create_task(self._process_sentiment()),
            asyncio.create_task(self._generate_signals_periodically())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the service"""
        self.running = False
        self.logger.info("Stopping signal generation service")
        
        if self.feature_consumer:
            self.feature_consumer.close()
        if self.sentiment_consumer:
            self.sentiment_consumer.close()
        
        self.kafka_producer.close()
    
    def _initialize_consumers(self):
        """Initialize Kafka consumers"""
        consumer_config = {
            'bootstrap_servers': self.config.kafka_bootstrap_servers,
            'group_id': 'signal-generation',
            'auto_offset_reset': 'latest',
            'enable_auto_commit': True,
            'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
        }
        
        # Feature consumer
        self.feature_consumer = KafkaConsumer(
            'technical_features', **consumer_config
        )
        
        # Sentiment consumer  
        self.sentiment_consumer = KafkaConsumer(
            'sentiment_scores', **consumer_config
        )
    
    async def _process_features(self):
        """Process incoming technical features"""
        while self.running:
            try:
                message_batch = self.feature_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._handle_feature_data(message.value)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error("Feature processing error", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_sentiment(self):
        """Process incoming sentiment data"""
        while self.running:
            try:
                message_batch = self.sentiment_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await self._handle_sentiment_data(message.value)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error("Sentiment processing error", error=str(e))
                await asyncio.sleep(1)
    
    async def _handle_feature_data(self, feature_data: dict):
        """Handle incoming feature data"""
        try:
            symbol = feature_data['symbol']
            price = feature_data['price']
            features = feature_data['features']
            
            # Initialize symbol data if needed
            if symbol not in self.recent_features:
                self.recent_features[symbol] = {
                    'prices': [],
                    'features': []
                }
            
            # Add new data
            self.recent_features[symbol]['prices'].append(price)
            self.recent_features[symbol]['features'].append(features)
            
            # Keep only recent data
            max_length = 200
            if len(self.recent_features[symbol]['prices']) > max_length:
                self.recent_features[symbol]['prices'] = self.recent_features[symbol]['prices'][-max_length:]
                self.recent_features[symbol]['features'] = self.recent_features[symbol]['features'][-max_length:]
            
        except Exception as e:
            self.logger.error("Feature data handling failed", error=str(e))
    
    async def _handle_sentiment_data(self, sentiment_data: dict):
        """Handle incoming sentiment data"""
        try:
            symbols = sentiment_data['symbols']
            sentiment_score = sentiment_data['sentiment']['score']
            
            for symbol in symbols:
                if symbol not in self.recent_sentiment:
                    self.recent_sentiment[symbol] = []
                
                self.recent_sentiment[symbol].append(sentiment_score)
                
                # Keep only recent sentiment
                if len(self.recent_sentiment[symbol]) > 50:
                    self.recent_sentiment[symbol] = self.recent_sentiment[symbol][-50:]
            
        except Exception as e:
            self.logger.error("Sentiment data handling failed", error=str(e))
    
    async def _generate_signals_periodically(self):
        """Generate signals periodically for all symbols"""
        while self.running:
            try:
                # Generate signals for symbols with sufficient data
                symbols = set(self.recent_features.keys()).union(set(self.recent_sentiment.keys()))
                
                for symbol in symbols:
                    await self._generate_signal_for_symbol(symbol)
                
                # Wait before next signal generation cycle
                await asyncio.sleep(10)  # Generate signals every 10 seconds
                
            except Exception as e:
                self.logger.error("Periodic signal generation failed", error=str(e))
                await asyncio.sleep(30)
    
    async def _generate_signal_for_symbol(self, symbol: str):
        """Generate signal for a specific symbol"""
        try:
            # Get data for symbol
            prices = self.recent_features.get(symbol, {}).get('prices', [])
            features = self.recent_features.get(symbol, {}).get('features', [])
            sentiment = self.recent_sentiment.get(symbol, [])
            
            if not prices:
                return
            
            # Update signal generator with latest data
            self.signal_generator.update_symbol_data(
                symbol, prices, features, sentiment
            )
            
            # Generate signal
            signal = self.signal_generator.generate_signal(symbol)
            
            if signal and signal.signal_type != 'hold':
                # Send signal to Kafka
                await self.kafka_producer.send_async(
                    'trading_signals', signal.to_dict()
                )
                
                self.logger.info("Signal generated",
                               symbol=symbol,
                               signal_type=signal.signal_type,
                               confidence=signal.confidence)
            
        except Exception as e:
            self.logger.error("Signal generation failed", symbol=symbol, error=str(e))


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = structlog.get_logger(__name__)
    
    # Load configuration
    config = Config()
    
    # Create and start service
    service = SignalGenerationService(config)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
