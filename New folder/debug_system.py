#!/usr/bin/env python3
"""
Debug script for AI Trading System
Tests each component individually to identify issues
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_kafka_producer():
    """Test Kafka producer functionality"""
    print("🔍 Testing Kafka Producer...")
    try:
        from shared.kafka.producer import KafkaDataProducer, TopicManager
        print("✅ Kafka producer classes imported successfully")
        
        # Test without actually connecting to Kafka
        print("✅ Kafka producer is ready (connection not tested without Kafka server)")
        return True
    except Exception as e:
        print(f"❌ Kafka producer error: {e}")
        return False

def test_services():
    """Test service imports"""
    print("\n🔍 Testing Services...")
    
    import importlib.util
    import os
    
    services = [
        ('Data Ingestion', 'services/data-ingestion/main.py'),
        ('Feature Engineering', 'services/feature-engineering/main.py'), 
        ('Signal Generation', 'services/signal-generation/main.py')
    ]
    
    for name, module_path in services:
        try:
            full_path = os.path.join(os.getcwd(), module_path)
            spec = importlib.util.spec_from_file_location(f"{name.lower().replace(' ', '_')}_main", full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {name} service imports OK")
        except Exception as e:
            print(f"❌ {name} service error: {e}")
            return False
    return True

def test_shared_modules():
    """Test shared modules"""
    print("\n🔍 Testing Shared Modules...")
    
    modules = [
        ('Config', 'shared.config'),
        ('Market Data Models', 'shared.models.market_data'),
        ('Database Utils', 'shared.utils.database'),
        ('Technical Indicators', 'shared.utils.technical_indicators')
    ]
    
    for name, module in modules:
        try:
            __import__(module)
            print(f"✅ {name} imports OK")
        except Exception as e:
            print(f"❌ {name} error: {e}")
            return False
    return True

def test_dependencies():
    """Test key dependencies"""
    print("\n🔍 Testing Key Dependencies...")
    
    deps = [
        ('Kafka Python', 'kafka'),
        ('Pandas', 'pandas'),
        ('NumPy', 'numpy'),
        ('TensorFlow', 'tensorflow'),
        ('PyTorch', 'torch'),
        ('Prometheus Client', 'prometheus_client'),
        ('StructLog', 'structlog')
    ]
    
    missing_critical = []
    
    for name, module in deps:
        try:
            __import__(module)
            print(f"✅ {name} available")
        except ImportError:
            print(f"⚠️  {name} not available (may be optional)")
            if module in ['kafka', 'pandas', 'numpy']:
                missing_critical.append(name)
        except Exception as e:
            print(f"❌ {name} error: {e}")
            missing_critical.append(name)
    
    if missing_critical:
        print(f"❌ Critical dependencies missing: {', '.join(missing_critical)}")
        return False
    return True

if __name__ == "__main__":
    print("🚀 AI Trading System Debug Report")
    print("=" * 50)
    
    all_good = True
    
    all_good &= test_dependencies()
    all_good &= test_shared_modules()
    all_good &= test_kafka_producer()
    all_good &= test_services()
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All systems operational! No issues found.")
    else:
        print("⚠️  Some issues detected. Check output above.")
    print("=" * 50)
