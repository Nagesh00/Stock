"""
Built-in Technical Indicators

Simple implementations of common technical indicators to avoid
external dependency issues with TA-Lib and pandas-ta.
"""
import pandas as pd
import numpy as np
from typing import Dict, Union


class TechnicalIndicators:
    """Built-in technical indicators without external dependencies"""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                  k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        return -100 * (highest_high - close) / (highest_high - lowest_low)
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=window).mean()
        mean_deviation = typical_price.rolling(window=window).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )
        
        return (typical_price - sma_tp) / (0.015 * mean_deviation)
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = np.where(close > close.shift(), volume, 
                      np.where(close < close.shift(), -volume, 0))
        return pd.Series(obv, index=close.index).cumsum()
    
    @staticmethod
    def momentum(data: pd.Series, window: int = 10) -> pd.Series:
        """Momentum"""
        return data.diff(window)
    
    @staticmethod
    def rate_of_change(data: pd.Series, window: int = 10) -> pd.Series:
        """Rate of Change"""
        return ((data - data.shift(window)) / data.shift(window)) * 100
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Union[pd.Series, Dict]]:
        """Calculate all indicators for OHLCV data"""
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df.get('volume', pd.Series(index=df.index))
        
        indicators = {}
        
        # Moving averages
        indicators['sma_20'] = TechnicalIndicators.sma(close, 20)
        indicators['sma_50'] = TechnicalIndicators.sma(close, 50)
        indicators['ema_12'] = TechnicalIndicators.ema(close, 12)
        indicators['ema_26'] = TechnicalIndicators.ema(close, 26)
        
        # Oscillators
        indicators['rsi'] = TechnicalIndicators.rsi(close)
        indicators['stochastic'] = TechnicalIndicators.stochastic(high, low, close)
        indicators['williams_r'] = TechnicalIndicators.williams_r(high, low, close)
        indicators['cci'] = TechnicalIndicators.cci(high, low, close)
        
        # Trend indicators
        indicators['macd'] = TechnicalIndicators.macd(close)
        indicators['bollinger'] = TechnicalIndicators.bollinger_bands(close)
        
        # Volume indicators
        if not volume.empty:
            indicators['obv'] = TechnicalIndicators.obv(close, volume)
        
        # Volatility indicators
        indicators['atr'] = TechnicalIndicators.atr(high, low, close)
        
        # Momentum indicators
        indicators['momentum'] = TechnicalIndicators.momentum(close)
        indicators['roc'] = TechnicalIndicators.rate_of_change(close)
        
        return indicators


# For backwards compatibility with the existing code
def calculate_indicators(df: pd.DataFrame) -> Dict[str, Union[pd.Series, Dict]]:
    """Wrapper function for backwards compatibility"""
    return TechnicalIndicators.calculate_all_indicators(df)
