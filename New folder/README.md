# 🚀 AI Stock Market Analysis System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://docker.com)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-Streaming-orange.svg)](https://kafka.apache.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-AI%20Models-orange.svg)](https://tensorflow.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-grade, microservices-based AI trading system designed for real-time market analysis and algorithmic trading with event-driven architecture.

## 🎯 Key Features

- **🤖 AI-Powered Predictions**: LSTM neural networks with attention mechanism + GARCH volatility forecasting
- **⚡ Real-time Processing**: Sub-second latency with Apache Kafka streaming
- **🛡️ Risk Management**: Comprehensive portfolio-level risk controls and position sizing
- **📊 Multi-Asset Support**: Stocks, indices, forex, and cryptocurrency markets
- **🔗 Multi-Broker Integration**: Zerodha, Angel One, Upstox, and global brokers
- **📈 Advanced Analytics**: 15+ built-in technical indicators and sentiment analysis
- **🐳 Production Ready**: Docker containers, Kubernetes deployment, monitoring with Grafana
- **🔒 Paper Trading**: Safe testing environment with simulated trading

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Ingestion │───▶│ Feature Engine  │───▶│ Signal Generation│
│   Service       │    │    Service      │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Apache Kafka Event Stream                    │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Risk Management │    │ Order Management│    │Portfolio Manager│
│    Service      │    │    Service      │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Services
- **Data Ingestion**: Real-time market data and news feeds
- **Feature Engineering**: Technical indicators and sentiment analysis  
- **Signal Generation**: AI models for predictions (LSTM, GARCH)
- **Risk Management**: Portfolio-level risk controls
- **Order Management**: Trade execution and broker integration
- **Portfolio Management**: Real-time P&L tracking

### Infrastructure Stack
- **Message Broker**: Apache Kafka for event streaming
- **Database**: TimescaleDB for high-performance time-series data
- **Stream Processing**: Apache Spark Streaming  
- **ML Framework**: TensorFlow/PyTorch for deep learning models
- **Containerization**: Docker + Kubernetes for scalable deployment
- **Monitoring**: Prometheus + Grafana for real-time metrics
- **Security**: HashiCorp Vault for secrets management

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Nagesh00/Stock.git
cd Stock
```

### 2. Setup Python Environment
```bash
python -m venv ai_trading_env

# Windows
ai_trading_env\Scripts\activate

# Linux/Mac  
source ai_trading_env/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your API keys:
# - Indian Market: Zerodha, Angel One, Upstox
# - Global Market: Polygon.io, Alpha Vantage, Finnhub
# - News APIs: News API, Tiingo
```

### 4. Start Infrastructure
```bash
# Start all infrastructure services
docker-compose up -d

# Or use management script
python scripts/manage.py start
```

### 5. Launch Trading Services

**Option A: VS Code (Recommended)**
1. Open in VS Code
2. `Ctrl+Shift+P` → "Tasks: Run Task"
3. Select individual services to start

**Option B: Command Line**
```bash
# Start services individually
python services/data-ingestion/main.py
python services/feature-engineering/main.py  
python services/signal-generation/main.py
```

### 6. Access Web Interfaces
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Kafka UI**: http://localhost:8080
- **Prometheus**: http://localhost:9090

## 📊 Supported Markets & Brokers

### Indian Market
- **Zerodha Kite Connect**: Stocks, derivatives, commodities
- **Angel One SmartAPI**: Multi-asset trading
- **Upstox API**: Real-time market data
- **Global Datafeeds**: Professional market data

### Global Markets  
- **Polygon.io**: US stocks, options, forex
- **Alpha Vantage**: Global equities and forex
- **Finnhub**: International market data
- **Interactive Brokers**: Global multi-asset

### Cryptocurrency
- **Binance**: Spot and futures trading
- **Coinbase Pro**: Major cryptocurrencies
- **KuCoin**: Altcoin trading

## 🤖 AI Models & Strategies

### Deep Learning Models
- **LSTM with Attention**: Price prediction with 65%+ accuracy
- **GARCH Models**: Volatility forecasting and risk estimation
- **Transformer Networks**: Multi-timeframe analysis
- **Ensemble Methods**: Combining multiple model predictions

### Technical Analysis
- **15+ Built-in Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands
- **Custom Indicators**: Proprietary technical analysis tools
- **Pattern Recognition**: Chart pattern detection
- **Volume Analysis**: Smart money flow detection

### Sentiment Analysis
- **FinBERT**: Financial news sentiment scoring
- **Social Media**: Twitter/Reddit sentiment tracking
- **News Impact**: Real-time news event analysis

## 🛡️ Risk Management

### Pre-Trade Controls
- Maximum position size limits (default: 10% of portfolio)
- Portfolio exposure constraints
- Price deviation checks
- Margin requirement validation

### Real-Time Monitoring
- Circuit breakers for excessive losses
- Volatility-based position adjustment
- Correlation monitoring across strategies
- Real-time P&L tracking with alerts

### Risk Metrics
- **Value at Risk (VaR)**: Portfolio risk quantification
- **Maximum Drawdown**: Historical loss limits
- **Sharpe Ratio**: Risk-adjusted returns
- **Beta Analysis**: Market correlation tracking

## 📈 Performance & Backtesting

### Backtesting Framework
- **Event-Driven Simulation**: Realistic market conditions
- **Transaction Costs**: Brokerage, slippage, impact costs
- **Multiple Timeframes**: Tick, minute, hourly, daily data
- **Walk-Forward Analysis**: Out-of-sample validation

### Performance Metrics
- **Returns**: Absolute and risk-adjusted performance
- **Drawdowns**: Maximum and average drawdown analysis  
- **Volatility**: Rolling volatility and risk metrics
- **Benchmark Comparison**: Against market indices

## 🚀 Deployment

### Development
```bash
# Start development environment
python scripts/manage.py dev
```

### Production
```bash
# Kubernetes deployment
kubectl apply -f infrastructure/kubernetes/

# Docker Swarm
docker stack deploy -c docker-compose.prod.yml trading
```

### Monitoring
- **Real-time Dashboards**: System health and trading performance
- **Alerts**: Slack/Email notifications for critical events
- **Logging**: Structured logging with ELK stack integration

## 🔧 Development

### VS Code Integration
- **Debug Configurations**: Pre-configured for all services
- **Tasks**: One-click service startup
- **Testing**: Integrated pytest runner
- **Code Quality**: Black formatting, type checking

### Testing
```bash
# Run all tests
python scripts/manage.py test

# Run specific test suite
pytest tests/test_models.py -v
```

### Code Quality
```bash
# Format code
black .

# Type checking  
mypy services/

# Run linting
flake8 services/ shared/
```

## 📚 Documentation

- **Getting Started**: `docs/getting-started.md`
- **API Documentation**: Auto-generated from code
- **Architecture Guide**: `docs/architecture.md`
- **Deployment Guide**: `docs/deployment.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Use at your own risk.

## 🙏 Acknowledgments

- **Financial Data Providers**: Zerodha, Alpha Vantage, Polygon.io
- **Open Source Libraries**: TensorFlow, Kafka, TimescaleDB
- **Community**: Contributors and testers

---

**Built with ❤️ for the trading community**

[![GitHub stars](https://img.shields.io/github/stars/Nagesh00/Stock?style=social)](https://github.com/Nagesh00/Stock/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Nagesh00/Stock?style=social)](https://github.com/Nagesh00/Stock/network/members)
