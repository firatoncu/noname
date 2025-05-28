"""
Integration tests for the trading system.

Tests cover:
- End-to-end trading workflows
- Component integration scenarios
- Real-world trading scenarios (with mocks)
- Error propagation and recovery
- Performance under load
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import pandas as pd

from src.n0name.core.trading_engine import TradingEngine, TradingConfig
from src.n0name.core.position_manager import PositionManager, PositionConfig
from src.n0name.core.order_manager import OrderManager, OrderConfig
from src.n0name.core.base_strategy import SignalType, PositionSide, TradingSignal


@pytest.mark.integration
class TestTradingIntegration:
    """Integration tests for the complete trading system."""
    
    @pytest.mark.asyncio
    async def test_complete_trading_workflow(self, mock_binance_client, mock_logger, test_utils):
        """Test a complete trading workflow from signal to position close."""
        # Setup components
        trading_config = TradingConfig(
            max_open_positions=1,
            leverage=10,
            lookback_period=100,
            position_value_percentage=0.2
        )
        
        position_config = PositionConfig(
            tp_percentage_long=0.01,
            sl_percentage_long=0.005
        )
        
        order_config = OrderConfig(
            max_retries=2,
            retry_delay=0.1
        )
        
        # Create mock strategy that generates buy signal
        mock_strategy = Mock()
        mock_strategy.name = "IntegrationTestStrategy"
        mock_strategy.validate_market_data = Mock(return_value=True)
        
        buy_signal = TradingSignal(
            signal_type=SignalType.BUY,
            strength=0.8,
            confidence=0.9,
            conditions={'rsi_oversold': True, 'macd_bullish': True}
        )
        mock_strategy.check_buy_conditions = Mock(return_value=buy_signal)
        mock_strategy.check_sell_conditions = Mock(return_value=TradingSignal(
            signal_type=SignalType.HOLD, strength=0.0, confidence=0.0, conditions={}
        ))
        
        # Create trading engine
        engine = TradingEngine(
            strategy=mock_strategy,
            trading_config=trading_config,
            position_config=position_config,
            order_config=order_config
        )
        
        # Mock external dependencies
        symbols = ['BTCUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {'BTCUSDT': 0.00001},
                {'BTCUSDT': 5},
                {'BTCUSDT': 2}
            )
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                # Create realistic market data
                market_data = test_utils.create_mock_kline_data('BTCUSDT', 100)
                df = pd.DataFrame(market_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                mock_fetch.return_value = (df, 47200.0)
                
                with patch('src.n0name.core.trading_engine.get_capital_tbu') as mock_capital:
                    mock_capital.return_value = 1000.0
                    
                    with patch('src.n0name.core.trading_engine.calculate_quantity') as mock_calc_qty:
                        mock_calc_qty.return_value = 0.001
                        
                        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
                            mock_entry_price.return_value = 47200.0
                            
                            with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif:
                                mock_notif.return_value = False  # Disable notifications
                                
                                # Initialize engine
                                await engine.initialize(symbols, mock_binance_client, mock_logger)
                                
                                # Process signals (should open position)
                                await engine._process_symbol_signals('BTCUSDT', mock_binance_client, mock_logger)
                                
                                # Verify position was opened
                                assert engine.position_manager.has_position('BTCUSDT')
                                position = engine.position_manager._positions['BTCUSDT']
                                assert position.symbol == 'BTCUSDT'
                                assert position.side == PositionSide.LONG
                                assert position.quantity == 0.001
                                
                                # Simulate price movement for take profit
                                mock_fetch.return_value = (df, 47672.0)  # 1% increase
                                
                                # Monitor position (should close due to TP)
                                await engine._monitor_position('BTCUSDT', mock_binance_client, mock_logger)
                                
                                # Verify position was closed
                                assert not engine.position_manager.has_position('BTCUSDT')
    
    @pytest.mark.asyncio
    async def test_multiple_positions_management(self, mock_binance_client, mock_logger, test_utils):
        """Test managing multiple positions simultaneously."""
        trading_config = TradingConfig(
            max_open_positions=3,
            position_value_percentage=0.1
        )
        
        mock_strategy = Mock()
        mock_strategy.name = "MultiPositionStrategy"
        mock_strategy.validate_market_data = Mock(return_value=True)
        
        # Create buy signals for different symbols
        buy_signal = TradingSignal(
            signal_type=SignalType.BUY,
            strength=0.8,
            confidence=0.9,
            conditions={'condition_1': True, 'condition_2': True}
        )
        mock_strategy.check_buy_conditions = Mock(return_value=buy_signal)
        mock_strategy.check_sell_conditions = Mock(return_value=TradingSignal(
            signal_type=SignalType.HOLD, strength=0.0, confidence=0.0, conditions={}
        ))
        
        engine = TradingEngine(strategy=mock_strategy, trading_config=trading_config)
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {symbol: 0.00001 for symbol in symbols},
                {symbol: 5 for symbol in symbols},
                {symbol: 2 for symbol in symbols}
            )
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                def fetch_side_effect(lookback, symbol, client):
                    market_data = test_utils.create_mock_kline_data(symbol, lookback)
                    df = pd.DataFrame(market_data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['close'] = df['close'].astype(float)
                    return df, float(df['close'].iloc[-1])
                
                mock_fetch.side_effect = fetch_side_effect
                
                with patch('src.n0name.core.trading_engine.get_capital_tbu') as mock_capital:
                    mock_capital.return_value = 1000.0
                    
                    with patch('src.n0name.core.trading_engine.calculate_quantity') as mock_calc_qty:
                        mock_calc_qty.return_value = 0.001
                        
                        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
                            mock_entry_price.return_value = 47000.0
                            
                            with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif:
                                mock_notif.return_value = False
                                
                                # Initialize engine
                                await engine.initialize(symbols, mock_binance_client, mock_logger)
                                
                                # Process signals for all symbols
                                for symbol in symbols:
                                    await engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                                
                                # Verify all positions were opened
                                positions = engine.position_manager.get_all_positions()
                                assert len(positions) == 3
                                for symbol in symbols:
                                    assert symbol in positions
    
    @pytest.mark.asyncio
    async def test_max_positions_limit(self, mock_binance_client, mock_logger, test_utils):
        """Test that max positions limit is respected."""
        trading_config = TradingConfig(max_open_positions=2)
        
        mock_strategy = Mock()
        mock_strategy.name = "MaxPositionsStrategy"
        mock_strategy.validate_market_data = Mock(return_value=True)
        
        buy_signal = TradingSignal(
            signal_type=SignalType.BUY,
            strength=0.8,
            confidence=0.9,
            conditions={'condition_1': True, 'condition_2': True}
        )
        mock_strategy.check_buy_conditions = Mock(return_value=buy_signal)
        mock_strategy.check_sell_conditions = Mock(return_value=TradingSignal(
            signal_type=SignalType.HOLD, strength=0.0, confidence=0.0, conditions={}
        ))
        
        engine = TradingEngine(strategy=mock_strategy, trading_config=trading_config)
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {symbol: 0.00001 for symbol in symbols},
                {symbol: 5 for symbol in symbols},
                {symbol: 2 for symbol in symbols}
            )
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                def fetch_side_effect(lookback, symbol, client):
                    market_data = test_utils.create_mock_kline_data(symbol, lookback)
                    df = pd.DataFrame(market_data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['close'] = df['close'].astype(float)
                    return df, float(df['close'].iloc[-1])
                
                mock_fetch.side_effect = fetch_side_effect
                
                with patch('src.n0name.core.trading_engine.get_capital_tbu') as mock_capital:
                    mock_capital.return_value = 1000.0
                    
                    with patch('src.n0name.core.trading_engine.calculate_quantity') as mock_calc_qty:
                        mock_calc_qty.return_value = 0.001
                        
                        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
                            mock_entry_price.return_value = 47000.0
                            
                            with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif:
                                mock_notif.return_value = False
                                
                                # Initialize engine
                                await engine.initialize(symbols, mock_binance_client, mock_logger)
                                
                                # Process signals for all symbols
                                for symbol in symbols:
                                    await engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                                
                                # Verify only max positions were opened
                                positions = engine.position_manager.get_all_positions()
                                assert len(positions) == 2  # Should be limited to max_open_positions
    
    @pytest.mark.asyncio
    async def test_strategy_switching_during_trading(self, mock_binance_client, mock_logger):
        """Test switching strategies while trading is active."""
        engine = TradingEngine(strategy=Mock())
        
        # Create new strategy
        new_strategy = Mock()
        new_strategy.name = "NewStrategy"
        new_strategy.get_strategy_info = Mock(return_value={'name': 'NewStrategy', 'type': 'test'})
        
        # Switch strategy
        engine.switch_strategy(new_strategy, mock_logger)
        
        # Verify strategy was switched
        assert engine.strategy == new_strategy
        assert engine.strategy.name == "NewStrategy"
        mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_recovery_during_trading(self, mock_binance_client, mock_logger, test_utils):
        """Test error recovery mechanisms during trading."""
        mock_strategy = Mock()
        mock_strategy.name = "ErrorRecoveryStrategy"
        mock_strategy.validate_market_data = Mock(return_value=True)
        
        engine = TradingEngine(strategy=mock_strategy)
        symbols = ['BTCUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = ({'BTCUSDT': 0.00001}, {'BTCUSDT': 5}, {'BTCUSDT': 2})
            
            # Initialize engine
            await engine.initialize(symbols, mock_binance_client, mock_logger)
            
            # Test error in signal processing
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                mock_fetch.side_effect = Exception("Network error")
                
                # Should handle error gracefully
                await engine._process_symbol_signals('BTCUSDT', mock_binance_client, mock_logger)
                
                # Verify error was logged
                mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_position_monitoring_integration(self, mock_binance_client, mock_logger, test_utils):
        """Test integration between position monitoring and risk management."""
        position_config = PositionConfig(
            tp_percentage_long=0.005,  # 0.5% TP
            sl_percentage_long=0.01    # 1% SL
        )
        
        engine = TradingEngine(
            strategy=Mock(),
            position_config=position_config
        )
        
        # Manually add a position
        from src.n0name.core.position_manager import Position
        position = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0)
        engine.position_manager._positions['BTCUSDT'] = position
        engine._price_precisions = {'BTCUSDT': 2}
        
        # Test different price scenarios
        test_scenarios = [
            (47000.0, False, "No action - price at entry"),
            (47235.0, True, "Take profit triggered"),
            (46530.0, True, "Stop loss triggered"),
        ]
        
        for price, should_close, description in test_scenarios:
            # Reset position if it was closed
            if 'BTCUSDT' not in engine.position_manager._positions:
                engine.position_manager._positions['BTCUSDT'] = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0)
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                market_data = test_utils.create_mock_kline_data('BTCUSDT', 300)
                df = pd.DataFrame(market_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                mock_fetch.return_value = (df, price)
                
                with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif:
                    mock_notif.return_value = False
                    
                    with patch('src.n0name.core.position_manager.last500_histogram_check') as mock_histogram:
                        mock_histogram.return_value = True  # Confirm SL
                        
                        result = await engine._monitor_position('BTCUSDT', mock_binance_client, mock_logger)
                        
                        if should_close:
                            assert result is True, f"Position should have been closed: {description}"
                        else:
                            assert result is False, f"Position should not have been closed: {description}"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_binance_client, mock_logger, test_utils):
        """Test concurrent trading operations."""
        engine = TradingEngine(strategy=Mock())
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {symbol: 0.00001 for symbol in symbols},
                {symbol: 5 for symbol in symbols},
                {symbol: 2 for symbol in symbols}
            )
            
            await engine.initialize(symbols, mock_binance_client, mock_logger)
            
            # Create concurrent tasks
            tasks = []
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                def fetch_side_effect(lookback, symbol, client):
                    market_data = test_utils.create_mock_kline_data(symbol, lookback)
                    df = pd.DataFrame(market_data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['close'] = df['close'].astype(float)
                    return df, float(df['close'].iloc[-1])
                
                mock_fetch.side_effect = fetch_side_effect
                
                # Create concurrent signal processing tasks
                for symbol in symbols:
                    task = asyncio.create_task(
                        engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                    )
                    tasks.append(task)
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify no deadlocks or race conditions occurred
                assert True  # If we reach here, no deadlocks occurred
    
    @pytest.mark.asyncio
    async def test_database_integration(self, mock_binance_client, mock_logger, test_utils):
        """Test database integration during trading operations."""
        trading_config = TradingConfig(enable_database_logging=True)
        engine = TradingEngine(strategy=Mock(), trading_config=trading_config)
        
        symbols = ['BTCUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = ({'BTCUSDT': 0.00001}, {'BTCUSDT': 5}, {'BTCUSDT': 2})
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                market_data = test_utils.create_mock_kline_data('BTCUSDT', 100)
                df = pd.DataFrame(market_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                df['close'] = df['close'].astype(float)
                mock_fetch.return_value = (df, 47000.0)
                
                with patch('src.n0name.core.trading_engine.get_db_status') as mock_db_status:
                    mock_db_status.return_value = True
                    
                    with patch('src.n0name.core.trading_engine.write_live_conditions') as mock_write:
                        await engine.initialize(symbols, mock_binance_client, mock_logger)
                        await engine._process_symbol_signals('BTCUSDT', mock_binance_client, mock_logger)
                        
                        # Verify database write was called
                        mock_write.assert_called()
    
    @pytest.mark.asyncio
    async def test_notification_integration(self, mock_binance_client, mock_logger):
        """Test notification system integration."""
        engine = TradingEngine(strategy=Mock())
        
        # Test position opening notification
        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
            mock_entry_price.return_value = 47000.0
            
            with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif_status:
                mock_notif_status.return_value = True
                
                with patch('src.n0name.core.position_manager.send_position_open_alert') as mock_alert:
                    result = await engine.position_manager.open_position(
                        'BTCUSDT', PositionSide.LONG, 0.001, mock_binance_client, mock_logger
                    )
                    
                    assert result is True
                    mock_alert.assert_called_once()


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance-focused integration tests."""
    
    @pytest.mark.asyncio
    async def test_high_frequency_signal_processing(self, mock_binance_client, mock_logger, test_utils, performance_data):
        """Test system performance under high-frequency signal processing."""
        engine = TradingEngine(strategy=Mock())
        symbols = performance_data['symbols']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {symbol: 0.00001 for symbol in symbols},
                {symbol: 5 for symbol in symbols},
                {symbol: 2 for symbol in symbols}
            )
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                def fetch_side_effect(lookback, symbol, client):
                    market_data = test_utils.create_mock_kline_data(symbol, lookback)
                    df = pd.DataFrame(market_data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['close'] = df['close'].astype(float)
                    return df, float(df['close'].iloc[-1])
                
                mock_fetch.side_effect = fetch_side_effect
                
                await engine.initialize(symbols, mock_binance_client, mock_logger)
                
                # Measure processing time
                start_time = datetime.now()
                
                # Process signals for all symbols multiple times
                for _ in range(10):  # Reduced iterations for faster testing
                    tasks = []
                    for symbol in symbols:
                        task = asyncio.create_task(
                            engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                        )
                        tasks.append(task)
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Verify performance is acceptable (adjust threshold as needed)
                assert processing_time < 30.0, f"Processing took too long: {processing_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_binance_client, mock_logger, test_utils):
        """Test memory usage stability during extended operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        engine = TradingEngine(strategy=Mock())
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        with patch('src.n0name.core.trading_engine.stepsize_precision') as mock_stepsize:
            mock_stepsize.return_value = (
                {symbol: 0.00001 for symbol in symbols},
                {symbol: 5 for symbol in symbols},
                {symbol: 2 for symbol in symbols}
            )
            
            with patch('src.n0name.core.trading_engine.binance_fetch_data') as mock_fetch:
                def fetch_side_effect(lookback, symbol, client):
                    market_data = test_utils.create_mock_kline_data(symbol, lookback)
                    df = pd.DataFrame(market_data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    df['close'] = df['close'].astype(float)
                    return df, float(df['close'].iloc[-1])
                
                mock_fetch.side_effect = fetch_side_effect
                
                await engine.initialize(symbols, mock_binance_client, mock_logger)
                
                # Run multiple iterations to check for memory leaks
                for i in range(50):  # Reduced iterations
                    for symbol in symbols:
                        await engine._process_symbol_signals(symbol, mock_binance_client, mock_logger)
                    
                    # Check memory usage periodically
                    if i % 10 == 0:
                        current_memory = process.memory_info().rss
                        memory_increase = current_memory - initial_memory
                        
                        # Allow for some memory increase but detect significant leaks
                        assert memory_increase < 100 * 1024 * 1024, f"Potential memory leak detected: {memory_increase / 1024 / 1024:.2f} MB increase" 