"""
Unit tests for the TradingEngine class.

Tests cover:
- Engine initialization and configuration
- Trading signal processing
- Position and order management integration
- Strategy switching
- Error handling and recovery
- Trading status and metrics
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from src.n0name.core.trading_engine import TradingEngine, TradingConfig
from src.n0name.core.base_strategy import SignalType, PositionSide, TradingSignal
from src.n0name.exceptions import TradingBotException


@pytest.mark.unit
class TestTradingEngine:
    """Test suite for TradingEngine."""
    
    def test_trading_engine_initialization(self, mock_strategy, trading_config, position_config, order_config):
        """Test TradingEngine initialization."""
        engine = TradingEngine(
            strategy=mock_strategy,
            trading_config=trading_config,
            position_config=position_config,
            order_config=order_config
        )
        
        assert engine.strategy == mock_strategy
        assert engine.config == trading_config
        assert engine.position_manager is not None
        assert engine.order_manager is not None
        assert not engine._is_running
        assert engine._symbols == []
    
    def test_trading_engine_default_configs(self, mock_strategy):
        """Test TradingEngine with default configurations."""
        engine = TradingEngine(strategy=mock_strategy)
        
        assert engine.strategy == mock_strategy
        assert isinstance(engine.config, TradingConfig)
        assert engine.position_manager is not None
        assert engine.order_manager is not None
    
    @pytest.mark.asyncio
    async def test_engine_initialization_with_symbols(self, trading_engine, mock_binance_client, mock_logger):
        """Test engine initialization with symbols."""
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        # Mock stepsize_precision function
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {'BTCUSDT': 0.00001, 'ETHUSDT': 0.0001},  # step_sizes
                {'BTCUSDT': 5, 'ETHUSDT': 4},  # quantity_precisions
                {'BTCUSDT': 2, 'ETHUSDT': 2}   # price_precisions
            )
            
            await trading_engine.initialize(symbols, mock_binance_client, mock_logger)
            
            assert trading_engine._symbols == symbols
            assert 'BTCUSDT' in trading_engine._step_sizes
            assert 'ETHUSDT' in trading_engine._step_sizes
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_engine_initialization_error_handling(self, trading_engine, mock_binance_client, mock_logger):
        """Test engine initialization error handling."""
        symbols = ['BTCUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await trading_engine.initialize(symbols, mock_binance_client, mock_logger)
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_start_trading(self, trading_engine, mock_binance_client, mock_logger):
        """Test starting the trading engine."""
        symbols = ['BTCUSDT']
        
        # Mock dependencies
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = ({'BTCUSDT': 0.00001}, {'BTCUSDT': 5}, {'BTCUSDT': 2})
            
            with patch.object(trading_engine, '_trading_loop') as mock_trading_loop:
                with patch.object(trading_engine, '_position_monitoring_loop') as mock_monitoring_loop:
                    mock_trading_loop.return_value = AsyncMock()
                    mock_monitoring_loop.return_value = AsyncMock()
                    
                    # Start trading
                    task = asyncio.create_task(trading_engine.start_trading(mock_binance_client, mock_logger))
                    await asyncio.sleep(0.1)  # Let it start
                    
                    assert trading_engine._is_running
                    
                    # Stop trading
                    trading_engine._is_running = False
                    await asyncio.sleep(0.1)  # Let it stop
                    task.cancel()
                    
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
    
    @pytest.mark.asyncio
    async def test_stop_trading(self, trading_engine):
        """Test stopping the trading engine."""
        trading_engine._is_running = True
        
        await trading_engine.stop_trading()
        
        assert not trading_engine._is_running
    
    @pytest.mark.asyncio
    async def test_process_symbol_signals_no_position(self, trading_engine, mock_binance_client, mock_logger, sample_market_data):
        """Test processing signals when no position exists."""
        symbol = 'BTCUSDT'
        trading_engine._symbols = [symbol]
        trading_engine._step_sizes = {symbol: 0.00001}
        trading_engine._quantity_precisions = {symbol: 5}
        
        # Mock dependencies
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (sample_market_data.df, sample_market_data.close_price)
            
            with patch('src.n0name.core.trading_engine.get_capital_tbu') as mock_capital:
                mock_capital.return_value = 1000.0
                
                with patch('src.n0name.core.trading_engine.calculate_quantity') as mock_calc_qty:
                    mock_calc_qty.return_value = 0.001
                    
                    # Configure strategy to return buy signal
                    buy_signal = TradingSignal(
                        signal_type=SignalType.BUY,
                        strength=0.8,
                        confidence=0.9,
                        conditions={'condition_1': True, 'condition_2': True}
                    )
                    trading_engine.strategy.buy_signal_result = buy_signal
                    
                    with patch.object(trading_engine, '_execute_trade') as mock_execute:
                        await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                        
                        mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_symbol_signals_with_existing_position(self, trading_engine, mock_binance_client, mock_logger):
        """Test processing signals when position already exists."""
        symbol = 'BTCUSDT'
        
        # Mock existing position
        trading_engine.position_manager.has_position = Mock(return_value=True)
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
            
            # Should not fetch data if position exists
            mock_fetch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_symbol_signals_max_positions_reached(self, trading_engine, mock_binance_client, mock_logger):
        """Test processing signals when max positions reached."""
        symbol = 'BTCUSDT'
        
        # Mock no existing position but max positions reached
        trading_engine.position_manager.has_position = Mock(return_value=False)
        trading_engine.position_manager.get_all_positions = Mock(return_value={
            'ETHUSDT': Mock(),
            'ADAUSDT': Mock(),
            'BNBUSDT': Mock()
        })
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
            
            # Should not fetch data if max positions reached
            mock_fetch.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_trade_success(self, trading_engine, mock_binance_client, mock_logger, sample_trading_signal):
        """Test successful trade execution."""
        symbol = 'BTCUSDT'
        side = PositionSide.LONG
        quantity = 0.001
        
        # Mock successful order
        order_result = Mock()
        order_result.success = True
        
        trading_engine.order_manager.create_market_order = AsyncMock(return_value=order_result)
        trading_engine.position_manager.open_position = AsyncMock(return_value=True)
        
        await trading_engine._execute_trade(symbol, side, quantity, mock_binance_client, mock_logger, sample_trading_signal)
        
        trading_engine.order_manager.create_market_order.assert_called_once()
        trading_engine.position_manager.open_position.assert_called_once()
        mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_trade_failure(self, trading_engine, mock_binance_client, mock_logger, sample_trading_signal):
        """Test failed trade execution."""
        symbol = 'BTCUSDT'
        side = PositionSide.LONG
        quantity = 0.001
        
        # Mock failed order
        order_result = Mock()
        order_result.success = False
        order_result.error_message = "Insufficient balance"
        
        trading_engine.order_manager.create_market_order = AsyncMock(return_value=order_result)
        trading_engine.position_manager.open_position = AsyncMock()
        
        await trading_engine._execute_trade(symbol, side, quantity, mock_binance_client, mock_logger, sample_trading_signal)
        
        trading_engine.order_manager.create_market_order.assert_called_once()
        trading_engine.position_manager.open_position.assert_not_called()
        mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_monitor_position(self, trading_engine, mock_binance_client, mock_logger, sample_market_data):
        """Test position monitoring."""
        symbol = 'BTCUSDT'
        trading_engine._price_precisions = {symbol: 2}
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (sample_market_data.df, sample_market_data.close_price)
            
            trading_engine.position_manager.monitor_position = AsyncMock(return_value=False)
            
            await trading_engine._monitor_position(symbol, mock_binance_client, mock_logger)
            
            trading_engine.position_manager.monitor_position.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_position_closed(self, trading_engine, mock_binance_client, mock_logger, sample_market_data):
        """Test position monitoring when position is closed."""
        symbol = 'BTCUSDT'
        trading_engine._price_precisions = {symbol: 2}
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (sample_market_data.df, sample_market_data.close_price)
            
            trading_engine.position_manager.monitor_position = AsyncMock(return_value=True)
            
            await trading_engine._monitor_position(symbol, mock_binance_client, mock_logger)
            
            mock_logger.info.assert_called_with(f"Position closed for {symbol}")
    
    def test_switch_strategy(self, trading_engine, mock_logger):
        """Test strategy switching."""
        old_strategy = trading_engine.strategy
        new_strategy = Mock()
        new_strategy.name = "NewStrategy"
        
        trading_engine.switch_strategy(new_strategy, mock_logger)
        
        assert trading_engine.strategy == new_strategy
        assert trading_engine.strategy != old_strategy
        mock_logger.info.assert_called()
    
    def test_get_trading_status(self, trading_engine):
        """Test getting trading status."""
        # Mock position and order managers
        trading_engine.position_manager.get_position_summary = Mock(return_value={'total_positions': 2})
        trading_engine.order_manager.get_statistics = Mock(return_value={'total_orders': 10})
        
        status = trading_engine.get_trading_status()
        
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'strategy' in status
        assert 'symbols' in status
        assert 'config' in status
        assert 'positions' in status
        assert 'orders' in status
    
    def test_update_config(self, trading_engine):
        """Test updating trading configuration."""
        new_config = TradingConfig(
            max_open_positions=5,
            leverage=20,
            lookback_period=1000
        )
        
        trading_engine.update_config(new_config)
        
        assert trading_engine.config == new_config
        assert trading_engine.config.max_open_positions == 5
        assert trading_engine.config.leverage == 20
    
    @pytest.mark.asyncio
    async def test_close_all_positions(self, trading_engine, mock_binance_client, mock_logger):
        """Test closing all positions."""
        # Mock positions
        positions = {
            'BTCUSDT': Mock(),
            'ETHUSDT': Mock()
        }
        trading_engine.position_manager.get_all_positions = Mock(return_value=positions)
        trading_engine.position_manager.close_position = AsyncMock()
        
        await trading_engine.close_all_positions(mock_binance_client, mock_logger, "Test reason")
        
        # Should call close_position for each symbol
        assert trading_engine.position_manager.close_position.call_count == 2
        mock_logger.info.assert_called()
    
    def test_get_strategy_info(self, trading_engine):
        """Test getting strategy information."""
        # Mock strategy info
        expected_info = {'name': 'MockStrategy', 'type': 'test'}
        trading_engine.strategy.get_strategy_info = Mock(return_value=expected_info)
        
        info = trading_engine.get_strategy_info()
        
        assert info == expected_info
        trading_engine.strategy.get_strategy_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trading_loop_error_handling(self, trading_engine, mock_binance_client, mock_logger):
        """Test trading loop error handling."""
        trading_engine._symbols = ['BTCUSDT']
        trading_engine._is_running = True
        
        with patch.object(trading_engine, '_process_symbol_signals') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            # Run one iteration of the trading loop
            try:
                await trading_engine._trading_loop(mock_binance_client, mock_logger)
            except Exception:
                pass  # Expected to handle the error
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_position_monitoring_loop_error_handling(self, trading_engine, mock_binance_client, mock_logger):
        """Test position monitoring loop error handling."""
        trading_engine._is_running = True
        
        # Mock positions
        positions = {'BTCUSDT': Mock()}
        trading_engine.position_manager.get_all_positions = Mock(return_value=positions)
        
        with patch.object(trading_engine, '_monitor_position') as mock_monitor:
            mock_monitor.side_effect = Exception("Monitoring error")
            
            # Run one iteration of the monitoring loop
            try:
                await trading_engine._position_monitoring_loop(mock_binance_client, mock_logger)
            except Exception:
                pass  # Expected to handle the error
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_insufficient_market_data_handling(self, trading_engine, mock_binance_client, mock_logger):
        """Test handling of insufficient market data."""
        symbol = 'BTCUSDT'
        trading_engine._symbols = [symbol]
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (None, None)  # Insufficient data
            
            # Mock strategy validation to return False
            trading_engine.strategy.validate_market_data = Mock(return_value=False)
            
            await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
            
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_database_logging_enabled(self, trading_engine, mock_binance_client, mock_logger, sample_market_data):
        """Test database logging when enabled."""
        symbol = 'BTCUSDT'
        trading_engine.config.enable_database_logging = True
        trading_engine._symbols = [symbol]
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (sample_market_data.df, sample_market_data.close_price)
            
            with patch('src.n0name.core.trading_engine.get_db_status') as mock_db_status:
                mock_db_status.return_value = True
                
                with patch('src.n0name.core.trading_engine.write_live_conditions') as mock_write:
                    await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                    
                    mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_signal_processing_with_conditions(self, trading_engine, mock_binance_client, mock_logger, sample_market_data):
        """Test signal processing with various condition combinations."""
        symbol = 'BTCUSDT'
        trading_engine._symbols = [symbol]
        trading_engine._step_sizes = {symbol: 0.00001}
        trading_engine._quantity_precisions = {symbol: 5}
        
        with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
            mock_fetch.return_value = (sample_market_data.df, sample_market_data.close_price)
            
            with patch('src.n0name.core.trading_engine.get_capital_tbu') as mock_capital:
                mock_capital.return_value = 1000.0
                
                with patch('src.n0name.core.trading_engine.calculate_quantity') as mock_calc_qty:
                    mock_calc_qty.return_value = 0.001
                    
                    # Test buy signal with partial conditions
                    buy_signal = TradingSignal(
                        signal_type=SignalType.BUY,
                        strength=0.8,
                        confidence=0.9,
                        conditions={'condition_1': True, 'condition_2': False}  # Not all conditions met
                    )
                    trading_engine.strategy.buy_signal_result = buy_signal
                    
                    with patch.object(trading_engine, '_execute_trade') as mock_execute:
                        await trading_engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                        
                        # Should not execute trade when not all conditions are met
                        mock_execute.assert_not_called()


@pytest.mark.unit
class TestTradingConfig:
    """Test suite for TradingConfig."""
    
    def test_trading_config_defaults(self):
        """Test TradingConfig default values."""
        config = TradingConfig()
        
        assert config.max_open_positions == 5
        assert config.leverage == 10
        assert config.lookback_period == 500
        assert config.position_value_percentage == 0.2
        assert config.enable_database_logging is True
        assert config.enable_notifications is True
    
    def test_trading_config_custom_values(self):
        """Test TradingConfig with custom values."""
        config = TradingConfig(
            max_open_positions=3,
            leverage=20,
            lookback_period=1000,
            position_value_percentage=0.1,
            enable_database_logging=False,
            enable_notifications=False
        )
        
        assert config.max_open_positions == 3
        assert config.leverage == 20
        assert config.lookback_period == 1000
        assert config.position_value_percentage == 0.1
        assert config.enable_database_logging is False
        assert config.enable_notifications is False 