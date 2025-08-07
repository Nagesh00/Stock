#!/usr/bin/env python3
"""
Quick test to verify that all modules can be imported properly
This helps VS Code understand the project structure
"""

if __name__ == "__main__":
    print("Testing module imports...")
    
    # Test services
    try:
        import services
        print("✅ services package")
    except ImportError as e:
        print(f"❌ services: {e}")
    
    # Test shared modules
    try:
        from shared.config import Config
        print("✅ shared.config")
    except ImportError as e:
        print(f"❌ shared.config: {e}")
    
    try:
        from shared.models.market_data import MarketTick
        print("✅ shared.models.market_data")
    except ImportError as e:
        print(f"❌ shared.models.market_data: {e}")
    
    # Test scripts
    try:
        import scripts
        print("✅ scripts package")
    except ImportError as e:
        print(f"❌ scripts: {e}")
    
    print("Module import test complete!")
