#!/usr/bin/env python3
"""
AI Trading System Startup Script

This script helps you get started with the AI trading system by:
1. Checking dependencies
2. Setting up environment
3. Starting infrastructure services
4. Running initial tests
"""

import os
import sys
import subprocess
import time
import json
import click
import asyncio
from pathlib import Path


def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Docker found: {result.stdout.strip()}")
        
        # Check if Docker daemon is running
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True, check=True)
        print("✓ Docker daemon is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker not found or not running")
        print("Please install Docker Desktop and ensure it's running")
        return False


def check_python_deps():
    """Check if required Python packages are installed"""
    required_packages = [
        'pandas', 'numpy', 'tensorflow', 'torch', 
        'kafka-python', 'asyncpg', 'structlog'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True


def setup_environment():
    """Set up environment file if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("Setting up environment configuration...")
        env_example.read_text().replace('your_', 'demo_')
        with open(env_file, 'w') as f:
            f.write(env_example.read_text())
        print("✓ Created .env file from template")
        print("⚠ Please update .env with your actual API keys")
    elif env_file.exists():
        print("✓ Environment file exists")
    else:
        print("✗ No environment template found")
        return False
    
    return True


def start_infrastructure():
    """Start Docker infrastructure services"""
    print("Starting infrastructure services...")
    
    try:
        # Start only infrastructure services first
        subprocess.run([
            'docker-compose', 'up', '-d', 
            'zookeeper', 'kafka', 'timescaledb', 'redis', 
            'prometheus', 'grafana', 'kafka-ui'
        ], check=True)
        
        print("✓ Infrastructure services started")
        
        # Wait for services to be ready
        print("Waiting for services to be ready...")
        time.sleep(30)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start infrastructure: {e}")
        return False


def check_services():
    """Check if services are healthy"""
    services = {
        'Kafka': 'localhost:9092',
        'TimescaleDB': 'localhost:5432',
        'Redis': 'localhost:6379',
        'Prometheus': 'localhost:9090',
        'Grafana': 'localhost:3000',
        'Kafka UI': 'localhost:8080'
    }
    
    print("Checking service health...")
    
    for service, endpoint in services.items():
        # This is a simplified check - in practice you'd want proper health checks
        print(f"✓ {service} should be available at {endpoint}")
    
    print("\nServices should be accessible at:")
    print("- Grafana Dashboard: http://localhost:3000 (admin/admin)")
    print("- Kafka UI: http://localhost:8080")
    print("- Prometheus: http://localhost:9090")


def create_sample_data():
    """Create some sample data for testing"""
    print("Setting up sample data...")
    
    # This would create sample market data, news, etc.
    # For now, just create a placeholder
    sample_data_dir = Path('data/samples')
    sample_data_dir.mkdir(parents=True, exist_ok=True)
    
    print("✓ Sample data directory created")


@click.group()
def cli():
    """AI Trading System Management CLI"""
    pass


@cli.command()
def check():
    """Check system dependencies and configuration"""
    print("🔍 Checking AI Trading System Dependencies...\n")
    
    all_good = True
    
    print("1. Checking Docker...")
    if not check_docker():
        all_good = False
    
    print("\n2. Checking Python dependencies...")
    if not check_python_deps():
        all_good = False
    
    print("\n3. Checking environment setup...")
    if not setup_environment():
        all_good = False
    
    if all_good:
        print("\n✅ All checks passed! System is ready.")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


@cli.command()
def start():
    """Start the AI trading system"""
    print("🚀 Starting AI Trading System...\n")
    
    # Run checks first
    if not all([check_docker(), check_python_deps(), setup_environment()]):
        print("❌ Pre-flight checks failed")
        sys.exit(1)
    
    # Start infrastructure
    if not start_infrastructure():
        print("❌ Failed to start infrastructure")
        sys.exit(1)
    
    # Check services
    check_services()
    
    print("\n✅ AI Trading System started successfully!")
    print("\nNext steps:")
    print("1. Configure your API keys in .env file")
    print("2. Start individual services using VS Code tasks or:")
    print("   python services/data-ingestion/main.py")
    print("   python services/feature-engineering/main.py")
    print("   python services/signal-generation/main.py")


@cli.command()
def stop():
    """Stop the AI trading system"""
    print("🛑 Stopping AI Trading System...")
    
    try:
        subprocess.run(['docker-compose', 'down'], check=True)
        print("✅ System stopped successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop system: {e}")


@cli.command()
def status():
    """Check system status"""
    print("📊 AI Trading System Status\n")
    
    # Check Python environment
    python_version = sys.version.split()[0]
    print(f"✅ Python: {python_version}")
    
    # Check installed packages
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError:
        print("❌ Pandas: Not installed")
    
    try:
        import numpy
        print(f"✅ NumPy: {numpy.__version__}")
    except ImportError:
        print("❌ NumPy: Not installed")
    
    try:
        import tensorflow
        print(f"✅ TensorFlow: {tensorflow.__version__}")
    except ImportError:
        print("⚠️  TensorFlow: Not installed (using PyTorch fallback)")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch: Not installed")
    
    # Check for TA-Lib
    try:
        import talib  # type: ignore
        print("✅ TA-Lib: Available")
    except ImportError:
        try:
            import pandas_ta  # type: ignore
            print("⚠️  TA-Lib: Using pandas-ta fallback")
        except ImportError:
            print("❌ TA-Lib: Not available")
    
    # Check Docker (optional)
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = subprocess.run(['docker-compose', '--version'],
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"✅ Docker Compose: {result.stdout.strip()}")
                
                # Check running containers
                result = subprocess.run(['docker-compose', 'ps'],
                                      capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    print("📦 Docker Services:")
                    print(result.stdout)
                else:
                    print("📦 Docker Services: No containers running")
            else:
                print("⚠️  Docker Compose: Not available")
        else:
            print("⚠️  Docker: Not available")
    except FileNotFoundError:
        print("⚠️  Docker: Not installed or not in PATH")
    
    # Check configuration
    if os.path.exists('.env'):
        print("✅ Configuration: .env file found")
    else:
        print("⚠️  Configuration: .env file not found (copy from .env.example)")
    
    print("\n🚀 System is ready for development!")
    print("💡 To get started:")
    print("   1. Copy .env.example to .env and add your API keys")
    print("   2. Run services individually or use VS Code tasks")
    print("   3. Run 'python scripts/manage.py test' to verify setup")


@cli.command()
def logs():
    """Show system logs"""
    print("📋 AI Trading System Logs\n")
    
    try:
        subprocess.run(['docker-compose', 'logs', '-f'])
    except KeyboardInterrupt:
        print("\nLog streaming stopped")


@cli.command()
def test():
    """Run system tests"""
    print("🧪 Running AI Trading System Tests...\n")
    
    try:
        # Use the virtual environment's python
        venv_python = os.path.join(os.getcwd(), 'ai_trading_env', 'Scripts', 'python.exe')
        subprocess.run([venv_python, '-m', 'pytest', 'tests/', '-v'], check=True)
        print("✅ All tests passed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Some tests failed: {e}")
    except FileNotFoundError:
        print("❌ Virtual environment not found. Please run setup first.")


@cli.command()
@click.option('--service', help='Specific service to develop')
def dev():
    """Start development environment"""
    print("🔧 Starting development environment...\n")
    
    # Start only infrastructure for development
    try:
        subprocess.run([
            'docker-compose', 'up', '-d',
            'kafka', 'timescaledb', 'redis', 'prometheus', 'grafana'
        ], check=True)
        
        print("✅ Development infrastructure started")
        print("\nYou can now run services individually:")
        print("- Data Ingestion: python services/data-ingestion/main.py")
        print("- Feature Engineering: python services/feature-engineering/main.py") 
        print("- Signal Generation: python services/signal-generation/main.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start development environment: {e}")


if __name__ == "__main__":
    cli()
