"""
Kafka Producer Utilities

High-performance, fault-tolerant Kafka producer for the trading system
with proper serialization, error handling, and monitoring.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from prometheus_client import Counter, Histogram, Gauge
import structlog


# Metrics
MESSAGES_SENT = Counter('kafka_messages_sent_total', 
                       'Total messages sent to Kafka', ['topic'])
MESSAGES_FAILED = Counter('kafka_messages_failed_total',
                         'Total failed messages', ['topic', 'error_type'])
SEND_LATENCY = Histogram('kafka_send_latency_seconds',
                        'Latency of Kafka message sends', ['topic'])
PRODUCER_CONNECTIONS = Gauge('kafka_producer_connections',
                           'Number of active Kafka producer connections')


class KafkaDataProducer:
    """
    High-performance Kafka producer for market data streaming
    
    Features:
    - Async and sync sending capabilities
    - Automatic retries with exponential backoff
    - Comprehensive monitoring and metrics
    - Proper serialization for financial data
    - Circuit breaker pattern for fault tolerance
    """
    
    def __init__(self, bootstrap_servers: str, **kwargs):
        self.bootstrap_servers = bootstrap_servers
        self.logger = structlog.get_logger(__name__)
        
        # Default producer configuration optimized for financial data
        default_config = {
            'bootstrap_servers': bootstrap_servers,
            'value_serializer': self._json_serializer,
            'key_serializer': self._string_serializer,
            'acks': 'all',  # Wait for all replicas to acknowledge
            'retries': 5,
            'retry_backoff_ms': 100,
            'batch_size': 16384,  # 16KB batches
            'linger_ms': 5,  # Wait up to 5ms for batching
            'buffer_memory': 33554432,  # 32MB buffer
            'compression_type': 'lz4',  # Fast compression
            'max_in_flight_requests_per_connection': 5,
            'enable_idempotence': True,  # Exactly-once semantics
            'request_timeout_ms': 30000,
            'delivery_timeout_ms': 120000,
        }
        
        # Merge with user-provided config
        config = {**default_config, **kwargs}
        
        try:
            self.producer = KafkaProducer(**config)
            PRODUCER_CONNECTIONS.inc()
            self.logger.info("Kafka producer initialized", 
                           bootstrap_servers=bootstrap_servers)
        except Exception as e:
            self.logger.error("Failed to initialize Kafka producer", error=str(e))
            raise
        
        # Circuit breaker state
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 10
        self.circuit_breaker_timeout = 60  # seconds
        self.circuit_breaker_last_failure = 0
        self.circuit_breaker_open = False
    
    def _json_serializer(self, data: Any) -> bytes:
        """Serialize data to JSON bytes with proper datetime handling"""
        def json_serial(obj):
            """JSON serializer for datetime objects"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        try:
            json_str = json.dumps(data, default=json_serial, separators=(',', ':'))
            return json_str.encode('utf-8')
        except Exception as e:
            self.logger.error("JSON serialization failed", error=str(e), data=data)
            raise
    
    def _string_serializer(self, data: str) -> bytes:
        """Serialize string to bytes"""
        if data is None:
            return None
        return data.encode('utf-8')
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker_open:
            return False
        
        # Check if timeout has passed
        if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_timeout:
            self.circuit_breaker_open = False
            self.circuit_breaker_failures = 0
            self.logger.info("Circuit breaker closed, attempting to resume")
            return False
        
        return True
    
    def _handle_failure(self, topic: str, error: Exception):
        """Handle send failure and update circuit breaker"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            self.logger.error("Circuit breaker opened due to failures",
                            failures=self.circuit_breaker_failures)
        
        # Record metrics
        error_type = type(error).__name__
        MESSAGES_FAILED.labels(topic=topic, error_type=error_type).inc()
        
        self.logger.error("Message send failed", 
                         topic=topic, error=str(error), error_type=error_type)
    
    def send(self, topic: str, value: Dict[str, Any], 
             key: Optional[str] = None, 
             callback: Optional[Callable] = None) -> bool:
        """
        Send message synchronously
        
        Args:
            topic: Kafka topic
            value: Message value (will be JSON serialized)
            key: Optional message key
            callback: Optional callback function
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Check circuit breaker
        if self._check_circuit_breaker():
            self.logger.warning("Circuit breaker open, dropping message", topic=topic)
            return False
        
        start_time = time.time()
        
        try:
            # Add timestamp if not present
            if isinstance(value, dict) and 'timestamp' not in value:
                value['timestamp'] = datetime.now().isoformat()
            
            # Send message
            future = self.producer.send(topic, value=value, key=key)
            
            # Wait for result (synchronous)
            record_metadata = future.get(timeout=30)
            
            # Record success metrics
            latency = time.time() - start_time
            SEND_LATENCY.labels(topic=topic).observe(latency)
            MESSAGES_SENT.labels(topic=topic).inc()
            
            self.logger.debug("Message sent successfully",
                            topic=topic, partition=record_metadata.partition,
                            offset=record_metadata.offset, latency=latency)
            
            # Reset circuit breaker on success
            if self.circuit_breaker_failures > 0:
                self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)
            
            # Call callback if provided
            if callback:
                callback(record_metadata, None)
            
            return True
            
        except KafkaTimeoutError as e:
            self._handle_failure(topic, e)
            if callback:
                callback(None, e)
            return False
            
        except KafkaError as e:
            self._handle_failure(topic, e)
            if callback:
                callback(None, e)
            return False
            
        except Exception as e:
            self._handle_failure(topic, e)
            if callback:
                callback(None, e)
            return False
    
    async def send_async(self, topic: str, value: Dict[str, Any], 
                        key: Optional[str] = None) -> bool:
        """
        Send message asynchronously
        
        Args:
            topic: Kafka topic
            value: Message value (will be JSON serialized)
            key: Optional message key
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Run synchronous send in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, topic, value, key)
    
    def send_batch(self, messages: list) -> Dict[str, int]:
        """
        Send multiple messages efficiently
        
        Args:
            messages: List of dicts with 'topic', 'value', and optional 'key'
            
        Returns:
            Dict with success/failure counts
        """
        results = {'success': 0, 'failed': 0}
        
        for msg in messages:
            topic = msg['topic']
            value = msg['value']
            key = msg.get('key')
            
            if self.send(topic, value, key):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def flush(self, timeout: Optional[float] = None):
        """
        Flush pending messages
        
        Args:
            timeout: Maximum time to wait for flush
        """
        try:
            self.producer.flush(timeout=timeout)
            self.logger.debug("Producer flushed successfully")
        except Exception as e:
            self.logger.error("Producer flush failed", error=str(e))
    
    def close(self):
        """Close the producer and clean up resources"""
        try:
            self.producer.close()
            PRODUCER_CONNECTIONS.dec()
            self.logger.info("Kafka producer closed")
        except Exception as e:
            self.logger.error("Error closing producer", error=str(e))
    
    def get_metadata(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get topic metadata"""
        try:
            metadata = self.producer.list_consumer_group_offsets()
            return metadata
        except Exception as e:
            self.logger.error("Failed to get metadata", topic=topic, error=str(e))
            return None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class TopicManager:
    """Manage Kafka topics for the trading system"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.logger = structlog.get_logger(__name__)
    
    def create_topics(self):
        """Create all required topics for the trading system"""
        from kafka.admin import KafkaAdminClient, NewTopic
        
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            client_id='topic_manager'
        )
        
        # Define topics with appropriate configurations
        topics = [
            # Market data topics
            NewTopic(name="market_data_raw", num_partitions=10, replication_factor=1),
            NewTopic(name="market_data_processed", num_partitions=10, replication_factor=1),
            NewTopic(name="order_book_updates", num_partitions=5, replication_factor=1),
            
            # News and sentiment
            NewTopic(name="financial_news", num_partitions=3, replication_factor=1),
            NewTopic(name="sentiment_scores", num_partitions=3, replication_factor=1),
            
            # Trading signals and orders
            NewTopic(name="trading_signals", num_partitions=5, replication_factor=1),
            NewTopic(name="risk_assessments", num_partitions=3, replication_factor=1),
            NewTopic(name="orders", num_partitions=5, replication_factor=1),
            NewTopic(name="trades", num_partitions=5, replication_factor=1),
            
            # Portfolio and performance
            NewTopic(name="positions", num_partitions=3, replication_factor=1),
            NewTopic(name="portfolio_updates", num_partitions=3, replication_factor=1),
            
            # System events
            NewTopic(name="system_events", num_partitions=3, replication_factor=1),
            NewTopic(name="alerts", num_partitions=3, replication_factor=1),
        ]
        
        try:
            # Create topics
            admin_client.create_topics(topics, validate_only=False)
            self.logger.info("Topics created successfully", count=len(topics))
            
        except Exception as e:
            self.logger.error("Failed to create topics", error=str(e))
        finally:
            admin_client.close()
