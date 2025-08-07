"""
Database Management Utilities

TimescaleDB database operations for the AI trading system
with proper connection pooling, error handling, and time-series optimizations.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager
import pandas as pd

import asyncpg
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, MetaData, Table, Column, String, Float, Integer, DateTime, Boolean
import structlog


class DatabaseManager:
    """Manages database connections and operations for the trading system"""
    
    def __init__(self, database_url: str, pool_size: int = 10):
        self.database_url = database_url
        self.pool_size = pool_size
        self.logger = structlog.get_logger(__name__)
        
        # Create async engine
        self.engine = create_async_engine(
            database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            pool_size=pool_size,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )
        
        # Create session factory
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create connection pool for direct asyncpg operations
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=self.pool_size,
                command_timeout=60
            )
            
            # Create tables if they don't exist
            await self.create_tables()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error("Database initialization failed", error=str(e))
            raise
    
    async def close(self):
        """Close database connections"""
        try:
            if self.pool:
                await self.pool.close()
            
            await self.engine.dispose()
            self.logger.info("Database connections closed")
            
        except Exception as e:
            self.logger.error("Error closing database connections", error=str(e))
    
    async def create_tables(self):
        """Create database tables with TimescaleDB optimizations"""
        
        # SQL for creating tables
        create_tables_sql = """
        -- Enable TimescaleDB extension
        CREATE EXTENSION IF NOT EXISTS timescaledb;
        
        -- Market data table
        CREATE TABLE IF NOT EXISTS market_data (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            price DOUBLE PRECISION,
            volume BIGINT,
            bid DOUBLE PRECISION,
            ask DOUBLE PRECISION,
            source TEXT,
            PRIMARY KEY (time, symbol)
        );
        
        -- Convert to hypertable (TimescaleDB)
        SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);
        
        -- Technical indicators table
        CREATE TABLE IF NOT EXISTS technical_indicators (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            indicator_name TEXT NOT NULL,
            value DOUBLE PRECISION,
            timeframe TEXT,
            parameters JSONB,
            PRIMARY KEY (time, symbol, indicator_name)
        );
        
        SELECT create_hypertable('technical_indicators', 'time', if_not_exists => TRUE);
        
        -- Trading signals table
        CREATE TABLE IF NOT EXISTS trading_signals (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            confidence DOUBLE PRECISION,
            price_target DOUBLE PRECISION,
            stop_loss DOUBLE PRECISION,
            model_name TEXT,
            features JSONB,
            reasoning TEXT,
            PRIMARY KEY (time, symbol)
        );
        
        SELECT create_hypertable('trading_signals', 'time', if_not_exists => TRUE);
        
        -- Orders table
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            order_type TEXT NOT NULL,
            price DOUBLE PRECISION,
            stop_price DOUBLE PRECISION,
            status TEXT NOT NULL,
            filled_quantity INTEGER DEFAULT 0,
            avg_fill_price DOUBLE PRECISION,
            time_in_force TEXT DEFAULT 'DAY'
        );
        
        -- Trades table
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            time TIMESTAMPTZ NOT NULL,
            order_id TEXT REFERENCES orders(order_id),
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            commission DOUBLE PRECISION DEFAULT 0,
            pnl DOUBLE PRECISION
        );
        
        -- Positions table
        CREATE TABLE IF NOT EXISTS positions (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            avg_price DOUBLE PRECISION NOT NULL,
            current_price DOUBLE PRECISION NOT NULL,
            unrealized_pnl DOUBLE PRECISION NOT NULL,
            realized_pnl DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (time, symbol)
        );
        
        SELECT create_hypertable('positions', 'time', if_not_exists => TRUE);
        
        -- Portfolio performance table
        CREATE TABLE IF NOT EXISTS portfolio_performance (
            time TIMESTAMPTZ NOT NULL PRIMARY KEY,
            total_value DOUBLE PRECISION NOT NULL,
            cash DOUBLE PRECISION NOT NULL,
            pnl DOUBLE PRECISION NOT NULL,
            drawdown DOUBLE PRECISION NOT NULL,
            num_positions INTEGER NOT NULL,
            leverage DOUBLE PRECISION DEFAULT 1.0
        );
        
        SELECT create_hypertable('portfolio_performance', 'time', if_not_exists => TRUE);
        
        -- News and sentiment table
        CREATE TABLE IF NOT EXISTS news_sentiment (
            time TIMESTAMPTZ NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            source TEXT NOT NULL,
            symbols TEXT[],
            sentiment_score DOUBLE PRECISION,
            sentiment_label TEXT,
            PRIMARY KEY (time, title)
        );
        
        SELECT create_hypertable('news_sentiment', 'time', if_not_exists => TRUE);
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON trading_signals (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_orders_symbol_time ON orders (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_positions_symbol_time ON positions (symbol, time DESC);
        CREATE INDEX IF NOT EXISTS idx_news_symbols ON news_sentiment USING GIN (symbols);
        
        -- Create continuous aggregates for common queries (TimescaleDB feature)
        CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1h
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('1 hour', time) AS bucket,
               symbol,
               FIRST(price, time) AS open,
               MAX(price) AS high,
               MIN(price) AS low,
               LAST(price, time) AS close,
               SUM(volume) AS volume
        FROM market_data
        GROUP BY bucket, symbol;
        
        CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1d
        WITH (timescaledb.continuous) AS
        SELECT time_bucket('1 day', time) AS bucket,
               symbol,
               FIRST(price, time) AS open,
               MAX(price) AS high,
               MIN(price) AS low,
               LAST(price, time) AS close,
               SUM(volume) AS volume
        FROM market_data
        GROUP BY bucket, symbol;
        
        -- Enable compression for older data
        SELECT add_compression_policy('market_data', INTERVAL '7 days');
        SELECT add_compression_policy('technical_indicators', INTERVAL '7 days');
        SELECT add_compression_policy('trading_signals', INTERVAL '30 days');
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(create_tables_sql)
            
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error("Failed to create database tables", error=str(e))
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn
    
    async def insert_market_data(self, data: List[Dict[str, Any]]) -> bool:
        """Insert market data efficiently using batch insert"""
        if not data:
            return True
        
        try:
            async with self.get_connection() as conn:
                # Prepare data for insertion
                records = [
                    (
                        record['timestamp'],
                        record['symbol'],
                        record['price'],
                        record['volume'],
                        record.get('bid'),
                        record.get('ask'),
                        record.get('source', 'unknown')
                    )
                    for record in data
                ]
                
                # Batch insert
                await conn.executemany(
                    """
                    INSERT INTO market_data (time, symbol, price, volume, bid, ask, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (time, symbol) DO UPDATE SET
                        price = EXCLUDED.price,
                        volume = EXCLUDED.volume,
                        bid = EXCLUDED.bid,
                        ask = EXCLUDED.ask,
                        source = EXCLUDED.source
                    """,
                    records
                )
            
            self.logger.debug("Market data inserted", count=len(data))
            return True
            
        except Exception as e:
            self.logger.error("Failed to insert market data", error=str(e))
            return False
    
    async def insert_trading_signal(self, signal: Dict[str, Any]) -> bool:
        """Insert trading signal"""
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO trading_signals 
                    (time, symbol, signal_type, confidence, price_target, stop_loss, model_name, features, reasoning)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (time, symbol) DO UPDATE SET
                        signal_type = EXCLUDED.signal_type,
                        confidence = EXCLUDED.confidence,
                        price_target = EXCLUDED.price_target,
                        stop_loss = EXCLUDED.stop_loss,
                        model_name = EXCLUDED.model_name,
                        features = EXCLUDED.features,
                        reasoning = EXCLUDED.reasoning
                    """,
                    signal['timestamp'],
                    signal['symbol'],
                    signal['signal_type'],
                    signal['confidence'],
                    signal.get('price_target'),
                    signal.get('stop_loss'),
                    signal.get('model_name'),
                    signal.get('features'),
                    signal.get('reasoning')
                )
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to insert trading signal", error=str(e))
            return False
    
    async def get_market_data(self, symbol: str, start_time: datetime, 
                             end_time: datetime, limit: int = 1000) -> pd.DataFrame:
        """Get market data for a symbol within time range"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT time, symbol, price, volume, bid, ask, source
                    FROM market_data
                    WHERE symbol = $1 AND time >= $2 AND time <= $3
                    ORDER BY time DESC
                    LIMIT $4
                    """,
                    symbol, start_time, end_time, limit
                )
            
            # Convert to DataFrame
            if rows:
                df = pd.DataFrame(rows)
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                return df.sort_index()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error("Failed to get market data", symbol=symbol, error=str(e))
            return pd.DataFrame()
    
    async def get_latest_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get latest prices for multiple symbols"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT ON (symbol) symbol, price
                    FROM market_data
                    WHERE symbol = ANY($1)
                    ORDER BY symbol, time DESC
                    """,
                    symbols
                )
            
            return {row['symbol']: row['price'] for row in rows}
            
        except Exception as e:
            self.logger.error("Failed to get latest prices", error=str(e))
            return {}
    
    async def get_trading_signals(self, symbol: str, start_time: datetime,
                                 end_time: datetime) -> pd.DataFrame:
        """Get trading signals for a symbol within time range"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT time, symbol, signal_type, confidence, price_target, 
                           stop_loss, model_name, features, reasoning
                    FROM trading_signals
                    WHERE symbol = $1 AND time >= $2 AND time <= $3
                    ORDER BY time DESC
                    """,
                    symbol, start_time, end_time
                )
            
            if rows:
                df = pd.DataFrame(rows)
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                return df.sort_index()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error("Failed to get trading signals", symbol=symbol, error=str(e))
            return pd.DataFrame()
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute custom query and return results"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error("Query execution failed", query=query, error=str(e))
            return []
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
                
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False
