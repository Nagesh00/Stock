"""
Performance monitoring and system metrics
"""
import psutil
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import aioredis
from prometheus_client import Gauge, Counter, Histogram


class SystemMonitor:
    """Monitor system performance and resource usage"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Prometheus metrics
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
        self.network_io = Gauge('system_network_io_bytes', 'Network I/O bytes', ['direction'])
        
        # Trading metrics
        self.signals_generated = Counter('trading_signals_total', 'Total trading signals generated', ['signal_type'])
        self.orders_placed = Counter('orders_placed_total', 'Total orders placed', ['order_type'])
        self.latency = Histogram('request_latency_seconds', 'Request latency in seconds', ['endpoint'])
    
    async def start_monitoring(self):
        """Start system monitoring"""
        self.redis_client = await aioredis.from_url(self.redis_url)
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_system_metrics())
        asyncio.create_task(self._monitor_trading_metrics())
    
    async def _monitor_system_metrics(self):
        """Monitor system resource usage"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.disk_usage.set(disk_percent)
                
                # Network I/O
                network = psutil.net_io_counters()
                self.network_io.labels(direction='sent').set(network.bytes_sent)
                self.network_io.labels(direction='recv').set(network.bytes_recv)
                
                # Store in Redis for historical tracking
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk_percent,
                    'network_sent': network.bytes_sent,
                    'network_recv': network.bytes_recv
                }
                
                await self.redis_client.lpush('system_metrics', json.dumps(metrics))
                await self.redis_client.ltrim('system_metrics', 0, 1000)  # Keep last 1000 entries
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                print(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_trading_metrics(self):
        """Monitor trading-specific metrics"""
        while True:
            try:
                # This would be populated by the trading services
                # For now, we'll just maintain the structure
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"Error monitoring trading metrics: {e}")
                await asyncio.sleep(60)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or (disk.used / disk.total) > 0.9:
                health_status = "warning"
            if cpu_percent > 95 or memory.percent > 95 or (disk.used / disk.total) > 0.95:
                health_status = "critical"
            
            return {
                'status': health_status,
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'available_memory': memory.available,
                'total_memory': memory.total
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def record_signal(self, signal_type: str):
        """Record a trading signal"""
        self.signals_generated.labels(signal_type=signal_type).inc()
    
    async def record_order(self, order_type: str):
        """Record an order placement"""
        self.orders_placed.labels(order_type=order_type).inc()
    
    async def record_latency(self, endpoint: str, latency: float):
        """Record request latency"""
        self.latency.labels(endpoint=endpoint).observe(latency)


async def main():
    """Run system monitor as standalone service"""
    monitor = SystemMonitor()
    await monitor.start_monitoring()
    
    # Keep running
    try:
        while True:
            health = await monitor.get_system_health()
            print(f"System Health: {health['status']} - CPU: {health['cpu_percent']:.1f}% - Memory: {health['memory_percent']:.1f}%")
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("Stopping system monitor...")


if __name__ == "__main__":
    asyncio.run(main())
