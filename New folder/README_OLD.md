# AI Stock Market Analysis System

A production-grade, microservices-based AI trading system designed for real-time market analysis and algorithmic trading.

## Architecture Overview

This system implements a distributed, event-driven architecture with the following key components:

### Core Services
- **Data Ingestion Service**: Real-time market data and news feeds
- **Feature Engineering Service**: Technical indicators and sentiment analysis
- **Signal Generation Service**: AI models for predictions (LSTM, GARCH)
- **Risk Management Service**: Portfolio-level risk controls
- **Order Management Service**: Trade execution and broker integration
- **Portfolio Management Service**: Real-time P&L tracking

### Technology Stack
- **Message Broker**: Apache Kafka
- **Stream Processing**: Apache Spark Streaming
- **Database**: TimescaleDB (PostgreSQL extension)
- **ML Framework**: TensorFlow/PyTorch
- **Containerization**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Security**: HashiCorp Vault

## Project Structure

```
ai-trading-system/
├── services/                 # Microservices
│   ├── data-ingestion/      # Market data collection
│   ├── feature-engineering/ # Technical indicators
│   ├── signal-generation/   # AI models
│   ├── risk-management/     # Risk controls
│   ├── order-management/    # Trade execution
│   └── portfolio-management/ # P&L tracking
├── shared/                  # Shared libraries
│   ├── models/             # Data models
│   ├── utils/              # Common utilities
│   └── kafka/              # Kafka helpers
├── infrastructure/         # Infrastructure as Code
│   ├── docker/            # Docker configurations
│   ├── kubernetes/        # K8s manifests
│   └── terraform/         # Cloud infrastructure
├── backtesting/           # Strategy validation
│   ├── engines/          # Backtesting frameworks
│   ├── strategies/       # Trading strategies
│   └── analysis/         # Performance analysis
├── tests/                # Test suites
├── notebooks/            # Research notebooks
└── docs/                 # Documentation
```

## Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Apache Kafka
- TimescaleDB

### Installation

1. **Clone and setup environment:**
```bash
python -m venv ai_trading_env
# Windows
ai_trading_env\Scripts\activate
# Linux/Mac
source ai_trading_env/bin/activate

pip install -r requirements.txt
```

2. **Start infrastructure services:**
```bash
docker-compose up -d kafka timescaledb
```

3. **Run services:**
```bash
# Start all microservices
python scripts/start_services.py

# Or run individually
python services/data-ingestion/main.py
python services/feature-engineering/main.py
python services/signal-generation/main.py
```

## Data Sources

### Indian Market APIs
- **Zerodha Kite Connect**: L1 quotes, market depth, historical data
- **Angel One SmartAPI**: Free API access with brokerage account
- **Global Datafeeds**: Institutional-grade low latency data
- **TrueData**: NSE/NFO/MCX data with various API types

### Global Market APIs
- **Polygon.io**: Real-time global market data (< 20ms latency)
- **Alpha Vantage**: Free tier for research and prototyping
- **Finnhub.io**: Comprehensive global data with WebSocket support

### Alternative Data
- **News Sentiment**: Real-time financial news analysis using FinBERT
- **Social Media**: Twitter/X sentiment analysis
- **Economic Indicators**: Macro data integration

## AI Models

### Time-Series Forecasting
- **GARCH Models**: Volatility clustering and forecasting
- **LSTM Networks**: Non-linear pattern recognition with attention mechanism
- **Multi-Modal Models**: Price + sentiment + volatility features

### Risk Management
- **Position Sizing**: Kelly Criterion and fixed fractional methods
- **Dynamic Stops**: ATR-based trailing stops
- **Portfolio Optimization**: Correlation analysis and diversification

## Backtesting Framework

### Event-Driven Engine
- Realistic simulation with proper time ordering
- Survivorship bias handling
- Transaction cost modeling
- Corporate actions processing

### Performance Metrics
- **Risk-Adjusted Returns**: Sharpe, Sortino, Calmar ratios
- **Drawdown Analysis**: Maximum drawdown tracking
- **Win/Loss Analysis**: Profit factor and win rate
- **Slippage Modeling**: Realistic execution costs

## Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
# Kubernetes deployment
kubectl apply -f infrastructure/kubernetes/
```

### Monitoring
- **Grafana Dashboards**: Real-time system metrics
- **Prometheus Alerts**: System health monitoring
- **Custom Metrics**: Trading performance tracking

## Risk Management

### Pre-Trade Controls
- Maximum position size limits
- Portfolio exposure constraints
- Price deviation checks
- Margin requirement validation

### Real-Time Monitoring
- Circuit breakers for excessive losses
- Volatility-based position adjustment
- Correlation monitoring across strategies
- Real-time P&L tracking

## Security

### Secrets Management
- HashiCorp Vault for API keys
- Encrypted configuration files
- Role-based access control
- Audit logging for all access

### Network Security
- Service mesh for inter-service communication
- TLS encryption for all connections
- API rate limiting and authentication
- Network policies in Kubernetes

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Performance Tests
```bash
pytest tests/performance/
```

## Documentation

- [Architecture Design](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Trading Strategies](docs/strategies.md)
- [Risk Management](docs/risk-management.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes only. Trading financial instruments carries risk of loss. Past performance does not guarantee future results. Use at your own risk.
