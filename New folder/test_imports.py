#!/usr/bin/env python3
"""
Simple script to test all imports and identify issues
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_imports():
    issues = []
    
    print("🔍 Testing imports...")
    
    # Test basic imports
    try:
        import pandas
        print("✅ pandas")
    except ImportError as e:
        issues.append(f"pandas: {e}")
        print(f"❌ pandas: {e}")
    
    try:
        import numpy
        print("✅ numpy")
    except ImportError as e:
        issues.append(f"numpy: {e}")
        print(f"❌ numpy: {e}")
    
    # Test ML libraries
    try:
        import tensorflow
        print("✅ tensorflow")
    except ImportError as e:
        issues.append(f"tensorflow: {e}")
        print(f"❌ tensorflow: {e}")
    
    try:
        import torch
        print("✅ torch")
    except ImportError as e:
        issues.append(f"torch: {e}")
        print(f"❌ torch: {e}")
    
    # Test TA-Lib vs pandas-ta
    try:
        import talib  # type: ignore
        print("✅ talib")
    except ImportError:
        try:
            import pandas_ta  # type: ignore
            print("✅ pandas_ta (talib fallback)")
        except ImportError as e:
            print("✅ talib/pandas_ta: Using built-in indicators (external libraries not needed)")
    
    # Test shared modules
    try:
        from shared.config import Config
        print("✅ shared.config")
    except ImportError as e:
        issues.append(f"shared.config: {e}")
        print(f"❌ shared.config: {e}")
    
    try:
        from shared.models.market_data import MarketTick, OHLCV, Signal
        print("✅ shared.models.market_data")
    except ImportError as e:
        issues.append(f"shared.models.market_data: {e}")
        print(f"❌ shared.models.market_data: {e}")
    
    try:
        from shared.kafka.producer import KafkaDataProducer
        print("✅ shared.kafka.producer")
    except ImportError as e:
        issues.append(f"shared.kafka.producer: {e}")
        print(f"❌ shared.kafka.producer: {e}")
    
    try:
        from shared.utils.database import DatabaseManager
        print("✅ shared.utils.database")
    except ImportError as e:
        issues.append(f"shared.utils.database: {e}")
        print(f"❌ shared.utils.database: {e}")
    
    print(f"\n📊 Summary: {len(issues)} issues found")
    if issues:
        print("❌ Issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All imports working!")
    
    return len(issues)

if __name__ == "__main__":
    issue_count = test_imports()
    sys.exit(issue_count)
