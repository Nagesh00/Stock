"""
Configuration Management

Centralized configuration for the AI trading system with environment-based
settings, secrets management, and validation.
"""

import os
from typing import List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging


@dataclass
class KafkaConfig:
    """Kafka configuration"""
    bootstrap_servers: str = "localhost:9092"
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    consumer_timeout_ms: int = 1000


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "postgresql://trading_user:trading_password@localhost:5432/trading_db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = "redis://localhost:6379"
    decode_responses: bool = True
    socket_keepalive: bool = True
    socket_keepalive_options: dict = field(default_factory=dict)
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class DataSourceConfig:
    """Data source configuration"""
    # Indian Market APIs
    zerodha_api_key: Optional[str] = None
    zerodha_api_secret: Optional[str] = None
    zerodha_access_token: Optional[str] = None
    
    angel_one_api_key: Optional[str] = None
    angel_one_api_secret: Optional[str] = None
    angel_one_client_id: Optional[str] = None
    
    upstox_api_key: Optional[str] = None
    upstox_api_secret: Optional[str] = None
    upstox_access_token: Optional[str] = None
    
    global_datafeeds_api_key: Optional[str] = None
    truedata_api_key: Optional[str] = None
    
    # Global Market APIs
    polygon_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    
    # News and Sentiment APIs
    news_api_key: Optional[str] = None
    tiingo_api_key: Optional[str] = None
    finbert_model_path: str = "ProsusAI/finbert"
    
    # Default symbols to track
    symbols: List[str] = field(default_factory=lambda: [
        "NSE:INFY", "NSE:RELIANCE", "NSE:TCS", "NSE:HDFCBANK", "NSE:ICICIBANK"
    ])
    
    # Data collection settings
    polling_interval: int = 1  # seconds for REST API polling
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10


@dataclass
class MLConfig:
    """Machine Learning configuration"""
    # Model paths
    lstm_model_path: str = "models/lstm_predictor.h5"
    garch_model_path: str = "models/garch_model.pkl"
    sentiment_model_path: str = "models/finbert"
    
    # Training parameters
    lstm_sequence_length: int = 60
    lstm_batch_size: int = 32
    lstm_epochs: int = 100
    lstm_validation_split: float = 0.2
    lstm_dropout_rate: float = 0.2
    
    # GARCH parameters
    garch_p: int = 1
    garch_q: int = 1
    garch_vol_target: Optional[float] = None
    
    # Feature engineering
    technical_indicators: List[str] = field(default_factory=lambda: [
        "SMA_20", "SMA_50", "EMA_12", "EMA_26", "MACD", "RSI", "BBANDS", "ATR"
    ])
    
    # Model retraining
    retrain_interval_days: int = 7
    minimum_training_samples: int = 1000
    
    # Prediction thresholds
    signal_confidence_threshold: float = 0.6
    volatility_threshold: float = 0.02


@dataclass
class RiskConfig:
    """Risk management configuration"""
    # Position sizing
    max_position_size: float = 0.1  # 10% of portfolio per position
    max_portfolio_risk: float = 0.02  # 2% portfolio risk per trade
    kelly_fraction: float = 0.25  # Use quarter Kelly for position sizing
    
    # Stop losses
    default_stop_loss_pct: float = 0.02  # 2% stop loss
    atr_stop_multiplier: float = 2.0  # 2x ATR for dynamic stops
    trailing_stop_enabled: bool = True
    
    # Portfolio limits
    max_correlation: float = 0.7  # Maximum correlation between positions
    max_sector_exposure: float = 0.3  # Maximum exposure to any sector
    max_drawdown_limit: float = 0.15  # 15% maximum drawdown circuit breaker
    
    # Daily limits
    max_daily_trades: int = 100
    max_daily_loss: float = 0.05  # 5% daily loss limit
    max_order_value: float = 100000  # Maximum single order value
    
    # Volatility controls
    volatility_lookback_days: int = 20
    high_volatility_threshold: float = 0.03
    low_volatility_threshold: float = 0.01


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 1000000  # $1M starting capital
    commission_per_trade: float = 5.0  # $5 per trade
    slippage_bps: float = 2.0  # 2 basis points slippage
    
    # Data range
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"
    
    # Performance metrics
    benchmark_symbol: str = "NSE:NIFTY50"
    risk_free_rate: float = 0.05  # 5% annual risk-free rate
    
    # Reporting
    generate_plots: bool = True
    save_trades: bool = True
    detailed_logs: bool = False


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    # Prometheus metrics
    metrics_port: int = 8000
    metrics_path: str = "/metrics"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # Health checks
    health_check_interval: int = 30
    health_check_timeout: int = 10
    
    # Alerting
    slack_webhook_url: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    alert_recipients: List[str] = field(default_factory=list)
    
    # Performance monitoring
    latency_threshold_ms: float = 100.0
    error_rate_threshold: float = 0.01  # 1% error rate threshold
    memory_usage_threshold: float = 0.8  # 80% memory usage threshold


@dataclass
class Config:
    """Main configuration class"""
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Component configurations
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Service settings
    data_ingestion_enabled: bool = True
    feature_engineering_enabled: bool = True
    signal_generation_enabled: bool = True
    risk_management_enabled: bool = True
    order_management_enabled: bool = True
    portfolio_management_enabled: bool = True
    
    def __post_init__(self):
        """Load configuration from environment variables"""
        self._load_from_environment()
        self._validate_config()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Environment
        self.environment = os.getenv("ENVIRONMENT", self.environment)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Kafka
        self.kafka.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", 
                                                self.kafka.bootstrap_servers)
        
        # Database
        self.database.url = os.getenv("DATABASE_URL", self.database.url)
        
        # Redis
        self.redis.url = os.getenv("REDIS_URL", self.redis.url)
        
        # Data sources - API keys from environment
        self.data_sources.zerodha_api_key = os.getenv("ZERODHA_API_KEY")
        self.data_sources.zerodha_api_secret = os.getenv("ZERODHA_API_SECRET")
        self.data_sources.angel_one_api_key = os.getenv("ANGEL_ONE_API_KEY")
        self.data_sources.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.data_sources.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.data_sources.news_api_key = os.getenv("NEWS_API_KEY")
        
        # Risk management
        max_risk = os.getenv("MAX_PORTFOLIO_RISK")
        if max_risk:
            self.risk.max_portfolio_risk = float(max_risk)
        
        max_position = os.getenv("MAX_POSITION_SIZE")
        if max_position:
            self.risk.max_position_size = float(max_position)
        
        # Monitoring
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            self.monitoring.log_level = log_level
        
        self.monitoring.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    def _validate_config(self):
        """Validate configuration values"""
        # Risk validation
        if self.risk.max_portfolio_risk > 0.1:  # More than 10% risk
            logging.warning("High portfolio risk configured: %f", 
                          self.risk.max_portfolio_risk)
        
        if self.risk.max_position_size > 0.2:  # More than 20% per position
            logging.warning("High position size configured: %f", 
                          self.risk.max_position_size)
        
        # Data source validation
        if self.environment == "production":
            if not any([self.data_sources.zerodha_api_key,
                       self.data_sources.angel_one_api_key,
                       self.data_sources.polygon_api_key]):
                raise ValueError("No data source API keys configured for production")
    
    @property
    def kafka_bootstrap_servers(self) -> str:
        """Get Kafka bootstrap servers"""
        return self.kafka.bootstrap_servers
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return self.database.url
    
    @property
    def polling_interval(self) -> int:
        """Get data polling interval"""
        return self.data_sources.polling_interval
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


def load_config() -> Config:
    """Load configuration with environment-specific settings"""
    config = Config()
    
    # Load environment-specific configuration files if they exist
    env_config_file = f"config/{config.environment}.yaml"
    if Path(env_config_file).exists():
        # Could load YAML config here if needed
        pass
    
    return config
