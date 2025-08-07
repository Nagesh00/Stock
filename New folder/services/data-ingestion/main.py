"""
Data Ingestion Service

Responsible for collecting real-time market data from various sources
and publishing it to Kafka topics for downstream processing.

Features:
- Multi-source data collection (brokers, data vendors, news APIs)
- Real-time WebSocket connections
- Data validation and quality checks
- Fault-tolerant design with retry mechanisms
- Prometheus metrics collection
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import aiohttp
import websockets
from kafka import KafkaProducer
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from shared.config import Config
from shared.models.market_data import MarketTick, NewsItem
from shared.kafka.producer import KafkaDataProducer
from shared.utils.logging import setup_logging


# Metrics
MESSAGES_PRODUCED = Counter('data_ingestion_messages_produced_total', 
                           'Total messages produced', ['source', 'symbol'])
INGESTION_LATENCY = Histogram('data_ingestion_latency_seconds',
                             'Latency of data ingestion', ['source'])
ACTIVE_CONNECTIONS = Gauge('data_ingestion_active_connections',
                          'Number of active WebSocket connections', ['source'])
ERRORS_TOTAL = Counter('data_ingestion_errors_total',
                      'Total errors encountered', ['source', 'error_type'])


@dataclass
class DataSource:
    """Configuration for a data source"""
    name: str
    url: str
    api_key: Optional[str] = None
    symbols: List[str] = None
    data_type: str = "market_data"  # market_data, news, sentiment
    connection_type: str = "websocket"  # websocket, rest, polling


class DataIngestionService:
    """Main service class for data ingestion"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.kafka_producer = KafkaDataProducer(config.kafka_bootstrap_servers)
        self.sources: Dict[str, DataSource] = {}
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.running = False
        
    def add_data_source(self, source: DataSource):
        """Add a new data source to the ingestion pipeline"""
        self.sources[source.name] = source
        self.logger.info("Added data source", source=source.name, 
                        symbols=source.symbols, data_type=source.data_type)
    
    async def start(self):
        """Start the data ingestion service"""
        self.running = True
        self.logger.info("Starting data ingestion service")
        
        # Start metrics server
        start_http_server(8000)
        
        # Start connections to all data sources
        tasks = []
        for source_name, source in self.sources.items():
            if source.connection_type == "websocket":
                task = asyncio.create_task(self._connect_websocket(source))
                tasks.append(task)
            elif source.connection_type == "polling":
                task = asyncio.create_task(self._poll_data_source(source))
                tasks.append(task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the data ingestion service"""
        self.running = False
        self.logger.info("Stopping data ingestion service")
        
        # Close all WebSocket connections
        for connection in self.active_connections.values():
            await connection.close()
        
        # Close Kafka producer
        self.kafka_producer.close()
    
    async def _connect_websocket(self, source: DataSource):
        """Connect to a WebSocket data source"""
        while self.running:
            try:
                self.logger.info("Connecting to WebSocket", source=source.name, url=source.url)
                
                headers = {}
                if source.api_key:
                    headers["Authorization"] = f"Bearer {source.api_key}"
                
                async with websockets.connect(
                    source.url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    
                    self.active_connections[source.name] = websocket
                    ACTIVE_CONNECTIONS.labels(source=source.name).inc()
                    
                    # Subscribe to symbols if required
                    if source.symbols:
                        subscribe_msg = self._create_subscription_message(source)
                        await websocket.send(json.dumps(subscribe_msg))
                        self.logger.info("Subscribed to symbols", 
                                       source=source.name, symbols=source.symbols)
                    
                    # Listen for messages
                    async for message in websocket:
                        await self._process_websocket_message(source, message)
                        
            except Exception as e:
                ERRORS_TOTAL.labels(source=source.name, error_type=type(e).__name__).inc()
                self.logger.error("WebSocket connection error", 
                                source=source.name, error=str(e))
                
                # Remove from active connections
                if source.name in self.active_connections:
                    del self.active_connections[source.name]
                    ACTIVE_CONNECTIONS.labels(source=source.name).dec()
                
                # Wait before retry
                await asyncio.sleep(5)
    
    async def _poll_data_source(self, source: DataSource):
        """Poll a REST API data source"""
        while self.running:
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    headers = {}
                    if source.api_key:
                        headers["Authorization"] = f"Bearer {source.api_key}"
                    
                    async with session.get(source.url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            await self._process_rest_data(source, data)
                            
                            # Record latency
                            latency = time.time() - start_time
                            INGESTION_LATENCY.labels(source=source.name).observe(latency)
                        else:
                            ERRORS_TOTAL.labels(source=source.name, 
                                              error_type="http_error").inc()
                            self.logger.error("HTTP error", source=source.name, 
                                            status=response.status)
                
                # Wait for next poll
                await asyncio.sleep(self.config.polling_interval)
                
            except Exception as e:
                ERRORS_TOTAL.labels(source=source.name, error_type=type(e).__name__).inc()
                self.logger.error("Polling error", source=source.name, error=str(e))
                await asyncio.sleep(5)
    
    async def _process_websocket_message(self, source: DataSource, message: str):
        """Process a message received from WebSocket"""
        try:
            data = json.loads(message)
            
            if source.data_type == "market_data":
                await self._process_market_data(source, data)
            elif source.data_type == "news":
                await self._process_news_data(source, data)
            else:
                self.logger.warning("Unknown data type", 
                                  source=source.name, data_type=source.data_type)
                
        except Exception as e:
            ERRORS_TOTAL.labels(source=source.name, error_type="processing_error").inc()
            self.logger.error("Message processing error", 
                            source=source.name, error=str(e))
    
    async def _process_rest_data(self, source: DataSource, data: dict):
        """Process data received from REST API"""
        # Similar to WebSocket processing but for REST data
        if source.data_type == "market_data":
            await self._process_market_data(source, data)
        elif source.data_type == "news":
            await self._process_news_data(source, data)
    
    async def _process_market_data(self, source: DataSource, data: dict):
        """Process market data and send to Kafka"""
        try:
            # Parse the data based on source format
            tick = self._parse_market_tick(source, data)
            if tick:
                # Send to Kafka
                topic = f"market_data_{tick.symbol.lower()}"
                await self.kafka_producer.send_async(topic, asdict(tick))
                
                MESSAGES_PRODUCED.labels(source=source.name, 
                                       symbol=tick.symbol).inc()
                
                self.logger.debug("Published market data", 
                                symbol=tick.symbol, price=tick.price)
        
        except Exception as e:
            ERRORS_TOTAL.labels(source=source.name, error_type="market_data_error").inc()
            self.logger.error("Market data processing error", error=str(e))
    
    async def _process_news_data(self, source: DataSource, data: dict):
        """Process news data and send to Kafka"""
        try:
            news_item = self._parse_news_item(source, data)
            if news_item:
                # Send to Kafka
                topic = "financial_news"
                await self.kafka_producer.send_async(topic, asdict(news_item))
                
                MESSAGES_PRODUCED.labels(source=source.name, 
                                       symbol="news").inc()
                
                self.logger.debug("Published news item", 
                                title=news_item.title[:50])
        
        except Exception as e:
            ERRORS_TOTAL.labels(source=source.name, error_type="news_data_error").inc()
            self.logger.error("News data processing error", error=str(e))
    
    def _parse_market_tick(self, source: DataSource, data: dict) -> Optional[MarketTick]:
        """Parse market data based on source format"""
        try:
            # This would be customized for each data source
            # Example for a generic format
            return MarketTick(
                symbol=data.get("symbol", "UNKNOWN"),
                price=float(data.get("price", 0)),
                volume=int(data.get("volume", 0)),
                bid=float(data.get("bid", 0)),
                ask=float(data.get("ask", 0)),
                timestamp=datetime.now(),
                source=source.name
            )
        except (ValueError, KeyError) as e:
            self.logger.error("Failed to parse market tick", 
                            source=source.name, error=str(e))
            return None
    
    def _parse_news_item(self, source: DataSource, data: dict) -> Optional[NewsItem]:
        """Parse news data based on source format"""
        try:
            return NewsItem(
                title=data.get("title", ""),
                content=data.get("content", ""),
                source=source.name,
                symbols=data.get("symbols", []),
                timestamp=datetime.now(),
                sentiment_score=data.get("sentiment", 0.0)
            )
        except (ValueError, KeyError) as e:
            self.logger.error("Failed to parse news item", 
                            source=source.name, error=str(e))
            return None
    
    def _create_subscription_message(self, source: DataSource) -> dict:
        """Create subscription message for WebSocket sources"""
        # This would be customized for each data source
        return {
            "action": "subscribe",
            "symbols": source.symbols,
            "type": source.data_type
        }


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = structlog.get_logger(__name__)
    
    # Load configuration
    config = Config()
    
    # Create service
    service = DataIngestionService(config)
    
    # Add data sources (these would come from configuration)
    # Example Indian market sources
    if config.zerodha_api_key:
        zerodha_source = DataSource(
            name="zerodha",
            url="wss://websocket.kite.trade",
            api_key=config.zerodha_api_key,
            symbols=["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"],
            data_type="market_data",
            connection_type="websocket"
        )
        service.add_data_source(zerodha_source)
    
    # Example news source
    if config.news_api_key:
        news_source = DataSource(
            name="financial_news",
            url="wss://newsapi.example.com/stream",
            api_key=config.news_api_key,
            data_type="news",
            connection_type="websocket"
        )
        service.add_data_source(news_source)
    
    try:
        # Start the service
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
