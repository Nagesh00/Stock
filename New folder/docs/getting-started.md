# Getting Started with AI Stock Market Analysis System

## Overview

You now have a production-grade AI Stock Market Analysis System with microservices architecture. This guide will help you get started quickly.

## Prerequisites

Before you begin, ensure you have:

1. **Docker Desktop** installed and running
2. **Python 3.9+** 
3. **Git** (for version control)
4. **Visual Studio Code** (recommended)

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your API keys:

```bash
copy .env.example .env
```

Edit `.env` file and add your API keys:
- **Indian Market**: Zerodha, Angel One, Upstox, Global Datafeeds
- **Global Market**: Polygon.io, Alpha Vantage, Finnhub
- **News/Sentiment**: News API, Tiingo

### 2. Start Infrastructure

Use the VS Code integrated terminal or command prompt:

```bash
# Option 1: Use the management script
python scripts/manage.py start

# Option 2: Use Docker Compose directly
docker-compose up -d
```

This starts:
- **Apache Kafka** (message streaming)
- **TimescaleDB** (time-series database) 
- **Redis** (caching)
- **Prometheus** (monitoring)
- **Grafana** (visualization)

### 3. Access Web Interfaces

Once services are running, access:

- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Kafka UI**: http://localhost:8080
- **Prometheus**: http://localhost:9090

### 4. Run Trading Services

You can run services individually using VS Code tasks:

1. **Ctrl+Shift+P** → "Tasks: Run Task"
2. Select:
   - "Start Data Ingestion Service"
   - "Start Feature Engineering Service" 
   - "Start Signal Generation Service"

Or run manually:

```bash
# Activate virtual environment first
ai_trading_env\Scripts\activate

# Set Python path
set PYTHONPATH=%CD%

# Run services
python services/data-ingestion/main.py
python services/feature-engineering/main.py
python services/signal-generation/main.py
```

## Architecture Components

### Core Services

1. **Data Ingestion Service** (`services/data-ingestion/`)
   - Connects to market data APIs
   - WebSocket and REST API support
   - Real-time data validation
   - Kafka message publishing

2. **Feature Engineering Service** (`services/feature-engineering/`)
   - Technical indicator calculation (SMA, RSI, MACD, etc.)
   - Sentiment analysis using FinBERT
   - Real-time feature computation
   - Time-series feature management

3. **Signal Generation Service** (`services/signal-generation/`)
   - LSTM models with attention mechanism
   - GARCH volatility forecasting
   - Multi-modal signal generation
   - Risk-adjusted predictions

### Infrastructure

- **Kafka**: Event streaming and service communication
- **TimescaleDB**: High-performance time-series database
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection
- **Grafana**: Real-time dashboards

## Configuration

### API Keys Setup

Add your API keys to `.env`:

```bash
# Indian Market
ZERODHA_API_KEY=your_key_here
ANGEL_ONE_API_KEY=your_key_here

# Global Market  
POLYGON_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here

# News & Sentiment
NEWS_API_KEY=your_key_here
```

### Risk Management

Configure risk parameters in `.env`:

```bash
MAX_PORTFOLIO_RISK=0.02    # 2% portfolio risk per trade
MAX_POSITION_SIZE=0.1      # 10% max position size
MAX_DAILY_LOSS=0.05        # 5% daily loss limit
MAX_DRAWDOWN_LIMIT=0.15    # 15% max drawdown circuit breaker
```

### Symbols to Track

Specify symbols in `.env`:

```bash
SYMBOLS=NSE:INFY,NSE:RELIANCE,NSE:TCS,NSE:HDFCBANK,NSE:ICICIBANK
```

## Development Workflow

### 1. Start Development Environment

```bash
# Start only infrastructure services
python scripts/manage.py dev
```

### 2. Debug Services in VS Code

1. Set breakpoints in code
2. **F5** → Select debug configuration:
   - "Debug Data Ingestion Service"
   - "Debug Feature Engineering Service"
   - "Debug Signal Generation Service"

### 3. Run Tests

```bash
# Run all tests
python scripts/manage.py test

# Or use VS Code Test Explorer
# Ctrl+Shift+P → "Python: Discover Tests"
```

### 4. Monitor Performance

- **Grafana**: Real-time metrics dashboards
- **Prometheus**: Raw metrics at :9090/metrics
- **Application logs**: Check service output for structured logs

## Data Flow

```
Market Data APIs → Data Ingestion → Kafka Topics → Feature Engineering → AI Models → Trading Signals
                                                                                           ↓
TimescaleDB ← Portfolio Management ← Risk Management ← Order Management ← Signal Processing
```

## Safety Features

### Built-in Risk Management

- **Position size limits** prevent over-exposure
- **Stop-loss automation** with ATR-based trailing stops
- **Portfolio-level circuit breakers** halt trading on excessive losses
- **Pre-trade risk checks** validate all orders

### Paper Trading Mode

Set `PAPER_TRADING=true` in `.env` to:
- Test strategies without real money
- Validate system performance  
- Debug trading logic
- Train on historical data

## Monitoring & Alerting

### Key Metrics to Monitor

- **Data ingestion latency** (< 100ms target)
- **Model prediction accuracy** (track drift)
- **Portfolio performance** (Sharpe ratio, drawdown)
- **System health** (memory, CPU, disk usage)

### Alerts Configuration

Configure Slack/email alerts in `.env`:

```bash
SLACK_WEBHOOK_URL=your_webhook_url
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
```

## Troubleshooting

### Common Issues

1. **Docker not starting**
   ```bash
   # Check Docker status
   docker --version
   docker ps
   ```

2. **Database connection errors**
   ```bash
   # Check TimescaleDB
   docker-compose logs timescaledb
   ```

3. **Kafka connection issues**
   ```bash
   # Check Kafka logs
   docker-compose logs kafka
   ```

4. **Python import errors**
   ```bash
   # Ensure virtual environment is activated
   ai_trading_env\Scripts\activate
   
   # Set Python path
   set PYTHONPATH=%CD%
   ```

### Getting Help

- Check service logs: `docker-compose logs [service_name]`
- Review application logs for structured error messages
- Use VS Code debugger to step through code
- Monitor Grafana dashboards for system health

## Next Steps

1. **Configure API Keys**: Add your actual trading API credentials
2. **Test with Paper Trading**: Validate system with simulated trades
3. **Customize Models**: Adjust AI model parameters for your strategy
4. **Set Risk Limits**: Configure appropriate risk management settings
5. **Scale Infrastructure**: Deploy to cloud when ready for production

## Production Deployment

For production deployment:

1. **Use Kubernetes** for container orchestration
2. **Implement secrets management** with HashiCorp Vault
3. **Set up monitoring** with comprehensive alerting
4. **Configure backup strategies** for data and models
5. **Implement CI/CD pipelines** for automated deployments

The system is designed to scale from development to production with minimal changes.
