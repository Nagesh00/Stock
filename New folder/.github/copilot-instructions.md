# Copilot Instructions for AI Stock Market Analysis System

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a production-grade AI Stock Market Analysis System built with microservices architecture. The system is designed for real-time trading with event-driven components, containerized deployment, and institutional-grade risk management.

## Architecture Patterns
- **Microservices Architecture**: Each service is autonomous and communicates via APIs
- **Event-Driven Design**: Uses Apache Kafka for message streaming
- **Containerization**: Docker containers for consistent deployment
- **Stream Processing**: Apache Spark for real-time data processing
- **Time-Series Storage**: TimescaleDB for high-performance market data storage

## Key Components
1. **Data Ingestion Service**: Connects to market data feeds and news APIs
2. **Feature Engineering Service**: Calculates technical indicators and sentiment scores
3. **Signal Generation Service**: AI models (LSTM, GARCH) for predictions
4. **Risk Management Service**: Portfolio-level risk controls and position sizing
5. **Order Management Service**: Trade execution and broker integration
6. **Portfolio Management Service**: Real-time P&L tracking and monitoring

## Technology Stack
- **Message Broker**: Apache Kafka for data streaming
- **Stream Processing**: Apache Spark Streaming
- **Database**: TimescaleDB for time-series data
- **ML Framework**: TensorFlow/PyTorch for LSTM models
- **Backtesting**: LEAN Engine or custom event-driven framework
- **Containerization**: Docker and Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Security**: HashiCorp Vault for secrets management

## Coding Guidelines
- Follow event-driven patterns for real-time processing
- Implement proper error handling and circuit breakers
- Use type hints and comprehensive logging
- Design for fault tolerance and graceful degradation
- Include comprehensive unit and integration tests
- Follow financial industry best practices for data handling
- Implement proper risk management safeguards

## Financial Domain Specifics
- Handle market data with proper timestamping
- Implement lookback bias prevention
- Use event-driven backtesting for realistic simulations
- Apply proper risk management (position sizing, stop losses)
- Account for transaction costs and slippage
- Implement portfolio-level diversification strategies
