"""
Logging Utilities

Structured logging configuration for the AI trading system
with proper formatting, levels, and integration with monitoring.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'console')
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=[handler],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Reduce noise from external libraries
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)


class TradingLogger:
    """Enhanced logger for trading operations"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def log_trade(self, symbol: str, side: str, quantity: int, 
                  price: float, order_id: str, **kwargs):
        """Log trade execution"""
        self.logger.info(
            "Trade executed",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_id=order_id,
            trade_value=quantity * price,
            **kwargs
        )
    
    def log_signal(self, symbol: str, signal_type: str, confidence: float,
                   model: str, **kwargs):
        """Log trading signal generation"""
        self.logger.info(
            "Signal generated",
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            model=model,
            **kwargs
        )
    
    def log_risk_event(self, event_type: str, symbol: str, 
                       risk_metric: str, value: float, threshold: float, **kwargs):
        """Log risk management events"""
        self.logger.warning(
            "Risk event triggered",
            event_type=event_type,
            symbol=symbol,
            risk_metric=risk_metric,
            value=value,
            threshold=threshold,
            breach_pct=(value - threshold) / threshold * 100,
            **kwargs
        )
    
    def log_performance(self, symbol: str, pnl: float, return_pct: float,
                       duration_hours: float, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            "Performance update",
            symbol=symbol,
            pnl=pnl,
            return_pct=return_pct,
            duration_hours=duration_hours,
            annualized_return=return_pct * (8760 / duration_hours) if duration_hours > 0 else 0,
            **kwargs
        )
    
    def log_data_quality(self, source: str, symbol: str, quality_metric: str,
                        value: float, **kwargs):
        """Log data quality issues"""
        self.logger.warning(
            "Data quality issue",
            source=source,
            symbol=symbol,
            quality_metric=quality_metric,
            value=value,
            **kwargs
        )
    
    def log_system_health(self, component: str, metric: str, value: float,
                         status: str, **kwargs):
        """Log system health metrics"""
        self.logger.info(
            "System health update",
            component=component,
            metric=metric,
            value=value,
            status=status,
            **kwargs
        )


def get_trading_logger(name: str) -> TradingLogger:
    """Get a trading-specific logger instance"""
    return TradingLogger(name)
