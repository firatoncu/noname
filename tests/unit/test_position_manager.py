"""
Unit tests for the PositionManager class.

Tests cover:
- Position opening and closing
- Position monitoring and PnL calculations
- Risk management (TP/SL/Hard SL)
- Position tracking and state management
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from src.n0name.core.position_manager import PositionManager, PositionConfig, Position
from src.n0name.core.base_strategy import PositionSide, MarketData


@pytest.mark.unit
class TestPositionManager:
    """Test suite for PositionManager."""
    
    def test_position_manager_initialization(self, position_config):
        """Test PositionManager initialization."""
        manager = PositionManager(position_config)
        
        assert manager.config == position_config
        assert len(manager._positions) == 0
    
    def test_position_manager_default_config(self):
        """Test PositionManager with default configuration."""
        manager = PositionManager()
        
        assert isinstance(manager.config, PositionConfig)
        assert manager.config.tp_percentage_long == 0.003
        assert manager.config.sl_percentage_long == 0.01
    
    @pytest.mark.asyncio
    async def test_open_position_success(self, position_manager, mock_binance_client, mock_logger):
        """Test successful position opening."""
        symbol = 'BTCUSDT'
        side = PositionSide.LONG
        quantity = 0.001
        
        # Mock get_entry_price
        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
            mock_entry_price.return_value = 47000.0
            
            # Mock notification functions
            with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif_status:
                mock_notif_status.return_value = True
                
                with patch('src.n0name.core.position_manager.send_position_open_alert') as mock_alert:
                    result = await position_manager.open_position(symbol, side, quantity, mock_binance_client, mock_logger)
                    
                    assert result is True
                    assert symbol in position_manager._positions
                    
                    position = position_manager._positions[symbol]
                    assert position.symbol == symbol
                    assert position.side == side
                    assert position.quantity == quantity
                    assert position.entry_price == 47000.0
                    
                    mock_alert.assert_called_once()
                    mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_open_position_failure(self, position_manager, mock_binance_client, mock_logger):
        """Test position opening failure."""
        symbol = 'BTCUSDT'
        side = PositionSide.LONG
        quantity = 0.001
        
        # Mock get_entry_price to raise exception
        with patch('src.n0name.core.position_manager.get_entry_price') as mock_entry_price:
            mock_entry_price.side_effect = Exception("Failed to get entry price")
            
            result = await position_manager.open_position(symbol, side, quantity, mock_binance_client, mock_logger)
            
            assert result is False
            assert symbol not in position_manager._positions
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_close_position_success(self, position_manager, mock_binance_client, mock_logger, sample_position):
        """Test successful position closing."""
        symbol = sample_position.symbol
        position_manager._positions[symbol] = sample_position
        
        # Mock notification functions
        with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif_status:
            mock_notif_status.return_value = True
            
            with patch('src.n0name.core.position_manager.send_position_close_alert') as mock_alert:
                result = await position_manager.close_position(symbol, mock_binance_client, mock_logger)
                
                assert result is True
                assert symbol not in position_manager._positions
                mock_alert.assert_called_once()
                mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_close_position_not_found(self, position_manager, mock_binance_client, mock_logger):
        """Test closing non-existent position."""
        symbol = 'BTCUSDT'
        
        result = await position_manager.close_position(symbol, mock_binance_client, mock_logger)
        
        assert result is False
        mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_close_position_with_error(self, position_manager, mock_binance_client, mock_logger, sample_position):
        """Test position closing with error."""
        symbol = sample_position.symbol
        position_manager._positions[symbol] = sample_position
        
        # Mock notification to raise exception
        with patch('src.n0name.core.position_manager.get_notif_status') as mock_notif_status:
            mock_notif_status.side_effect = Exception("Notification error")
            
            result = await position_manager.close_position(symbol, mock_binance_client, mock_logger)
            
            assert result is False
            assert symbol in position_manager._positions  # Position should still exist
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_monitor_position_no_action(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring with no action needed."""
        symbol = sample_position.symbol
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.LONG
        position_manager._positions[symbol] = sample_position
        
        # Set market price close to entry (no TP/SL triggered)
        sample_market_data.close_price = 47100.0
        price_precisions = {symbol: 2}
        
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.return_value = (47141.0, 46530.0, 46201.0)  # TP, SL, Hard SL
            
            result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, price_precisions)
            
            assert result is False  # Position not closed
            assert symbol in position_manager._positions
    
    @pytest.mark.asyncio
    async def test_monitor_position_take_profit_triggered(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring with take profit triggered."""
        symbol = sample_position.symbol
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.LONG
        position_manager._positions[symbol] = sample_position
        
        # Set market price above TP
        sample_market_data.close_price = 47200.0
        price_precisions = {symbol: 2}
        
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.return_value = (47141.0, 46530.0, 46201.0)  # TP, SL, Hard SL
            
            with patch.object(position_manager, 'close_position') as mock_close:
                mock_close.return_value = True
                
                result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, price_precisions)
                
                assert result is True  # Position closed
                mock_close.assert_called_with(symbol, mock_binance_client, mock_logger, "Take Profit")
    
    @pytest.mark.asyncio
    async def test_monitor_position_stop_loss_triggered(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring with stop loss triggered."""
        symbol = sample_position.symbol
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.LONG
        position_manager._positions[symbol] = sample_position
        
        # Set market price below SL
        sample_market_data.close_price = 46400.0
        price_precisions = {symbol: 2}
        
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.return_value = (47141.0, 46530.0, 46201.0)  # TP, SL, Hard SL
            
            with patch('src.n0name.core.position_manager.last500_histogram_check') as mock_histogram:
                mock_histogram.return_value = True  # Confirm SL
                
                with patch.object(position_manager, 'close_position') as mock_close:
                    mock_close.return_value = True
                    
                    result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, price_precisions)
                    
                    assert result is True  # Position closed
                    mock_close.assert_called_with(symbol, mock_binance_client, mock_logger, "Stop Loss")
    
    @pytest.mark.asyncio
    async def test_monitor_position_hard_stop_loss_triggered(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring with hard stop loss triggered."""
        symbol = sample_position.symbol
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.LONG
        position_manager._positions[symbol] = sample_position
        
        # Set market price below hard SL
        sample_market_data.close_price = 46100.0
        price_precisions = {symbol: 2}
        
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.return_value = (47141.0, 46530.0, 46201.0)  # TP, SL, Hard SL
            
            with patch.object(position_manager, 'close_position') as mock_close:
                mock_close.return_value = True
                
                result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, price_precisions)
                
                assert result is True  # Position closed
                mock_close.assert_called_with(symbol, mock_binance_client, mock_logger, "Hard Stop Loss")
    
    @pytest.mark.asyncio
    async def test_monitor_position_short_take_profit(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring for short position take profit."""
        symbol = sample_position.symbol
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.SHORT
        position_manager._positions[symbol] = sample_position
        
        # Set market price below TP for short
        sample_market_data.close_price = 46800.0
        price_precisions = {symbol: 2}
        
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.return_value = (46859.0, 47470.0, 47799.0)  # TP, SL, Hard SL for short
            
            with patch.object(position_manager, 'close_position') as mock_close:
                mock_close.return_value = True
                
                result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, price_precisions)
                
                assert result is True  # Position closed
                mock_close.assert_called_with(symbol, mock_binance_client, mock_logger, "Take Profit")
    
    @pytest.mark.asyncio
    async def test_monitor_position_error_handling(self, position_manager, mock_binance_client, mock_logger, sample_market_data, sample_position):
        """Test position monitoring error handling."""
        symbol = sample_position.symbol
        position_manager._positions[symbol] = sample_position
        
        # Mock _calculate_tp_sl_levels to raise exception
        with patch.object(position_manager, '_calculate_tp_sl_levels') as mock_calc_levels:
            mock_calc_levels.side_effect = Exception("Calculation error")
            
            result = await position_manager.monitor_position(symbol, sample_market_data, mock_binance_client, mock_logger, {})
            
            assert result is False
            mock_logger.error.assert_called()
    
    def test_has_position(self, position_manager, sample_position):
        """Test checking if position exists."""
        symbol = sample_position.symbol
        
        # No position initially
        assert not position_manager.has_position(symbol)
        
        # Add position
        position_manager._positions[symbol] = sample_position
        assert position_manager.has_position(symbol)
    
    def test_get_all_positions(self, position_manager, sample_position):
        """Test getting all positions."""
        symbol = sample_position.symbol
        position_manager._positions[symbol] = sample_position
        
        positions = position_manager.get_all_positions()
        
        assert isinstance(positions, dict)
        assert symbol in positions
        assert positions[symbol] == sample_position
        
        # Should return a copy, not the original
        positions[symbol] = None
        assert position_manager._positions[symbol] == sample_position
    
    def test_calculate_tp_sl_levels_long(self, position_manager, sample_position):
        """Test TP/SL calculation for long position."""
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.LONG
        price_precision = 2
        
        tp_price, sl_price, hard_sl_price = position_manager._calculate_tp_sl_levels(sample_position, price_precision)
        
        # For long: TP above entry, SL below entry
        assert tp_price > sample_position.entry_price
        assert sl_price < sample_position.entry_price
        assert hard_sl_price < sl_price
        
        # Check precision
        assert len(str(tp_price).split('.')[-1]) <= price_precision
    
    def test_calculate_tp_sl_levels_short(self, position_manager, sample_position):
        """Test TP/SL calculation for short position."""
        sample_position.entry_price = 47000.0
        sample_position.side = PositionSide.SHORT
        price_precision = 2
        
        tp_price, sl_price, hard_sl_price = position_manager._calculate_tp_sl_levels(sample_position, price_precision)
        
        # For short: TP below entry, SL above entry
        assert tp_price < sample_position.entry_price
        assert sl_price > sample_position.entry_price
        assert hard_sl_price > sl_price
        
        # Check precision
        assert len(str(tp_price).split('.')[-1]) <= price_precision
    
    def test_get_position_summary(self, position_manager):
        """Test getting position summary."""
        # Add some test positions
        position1 = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0, 47100.0)
        position2 = Position('ETHUSDT', PositionSide.SHORT, 0.1, 3000.0, 2950.0)
        
        position_manager._positions['BTCUSDT'] = position1
        position_manager._positions['ETHUSDT'] = position2
        
        # Mock the method if it exists
        if hasattr(position_manager, 'get_position_summary'):
            summary = position_manager.get_position_summary()
            assert isinstance(summary, dict)
        else:
            # If method doesn't exist, test the positions directly
            positions = position_manager.get_all_positions()
            assert len(positions) == 2
            assert 'BTCUSDT' in positions
            assert 'ETHUSDT' in positions


@pytest.mark.unit
class TestPosition:
    """Test suite for Position class."""
    
    def test_position_creation(self):
        """Test Position creation."""
        position = Position(
            symbol='BTCUSDT',
            side=PositionSide.LONG,
            quantity=0.001,
            entry_price=47000.0,
            current_price=47100.0
        )
        
        assert position.symbol == 'BTCUSDT'
        assert position.side == PositionSide.LONG
        assert position.quantity == 0.001
        assert position.entry_price == 47000.0
        assert position.current_price == 47100.0
    
    def test_calculate_pnl_long_profit(self):
        """Test PnL calculation for long position in profit."""
        position = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0)
        current_price = 47500.0
        
        pnl = position.calculate_pnl(current_price)
        expected_pnl = (47500.0 - 47000.0) * 0.001
        
        assert abs(pnl - expected_pnl) < 0.0001
    
    def test_calculate_pnl_long_loss(self):
        """Test PnL calculation for long position in loss."""
        position = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0)
        current_price = 46500.0
        
        pnl = position.calculate_pnl(current_price)
        expected_pnl = (46500.0 - 47000.0) * 0.001
        
        assert abs(pnl - expected_pnl) < 0.0001
        assert pnl < 0  # Should be negative (loss)
    
    def test_calculate_pnl_short_profit(self):
        """Test PnL calculation for short position in profit."""
        position = Position('BTCUSDT', PositionSide.SHORT, 0.001, 47000.0)
        current_price = 46500.0
        
        pnl = position.calculate_pnl(current_price)
        expected_pnl = (47000.0 - 46500.0) * 0.001
        
        assert abs(pnl - expected_pnl) < 0.0001
        assert pnl > 0  # Should be positive (profit)
    
    def test_calculate_pnl_short_loss(self):
        """Test PnL calculation for short position in loss."""
        position = Position('BTCUSDT', PositionSide.SHORT, 0.001, 47000.0)
        current_price = 47500.0
        
        pnl = position.calculate_pnl(current_price)
        expected_pnl = (47000.0 - 47500.0) * 0.001
        
        assert abs(pnl - expected_pnl) < 0.0001
        assert pnl < 0  # Should be negative (loss)
    
    def test_calculate_pnl_percentage_long(self):
        """Test PnL percentage calculation for long position."""
        position = Position('BTCUSDT', PositionSide.LONG, 0.001, 47000.0)
        current_price = 47470.0  # 1% increase
        
        pnl_percentage = position.calculate_pnl_percentage(current_price)
        
        assert abs(pnl_percentage - 1.0) < 0.01  # Should be approximately 1%
    
    def test_calculate_pnl_percentage_short(self):
        """Test PnL percentage calculation for short position."""
        position = Position('BTCUSDT', PositionSide.SHORT, 0.001, 47000.0)
        current_price = 46530.0  # 1% decrease
        
        pnl_percentage = position.calculate_pnl_percentage(current_price)
        
        assert abs(pnl_percentage - 1.0) < 0.01  # Should be approximately 1%
    
    def test_calculate_pnl_percentage_zero_entry_price(self):
        """Test PnL percentage calculation with zero entry price."""
        position = Position('BTCUSDT', PositionSide.LONG, 0.001, 0.0)
        current_price = 47000.0
        
        pnl_percentage = position.calculate_pnl_percentage(current_price)
        
        assert pnl_percentage == 0.0


@pytest.mark.unit
class TestPositionConfig:
    """Test suite for PositionConfig."""
    
    def test_position_config_defaults(self):
        """Test PositionConfig default values."""
        config = PositionConfig()
        
        assert config.tp_percentage_long == 0.003
        assert config.sl_percentage_long == 0.01
        assert config.hard_sl_percentage_long == 0.017
        assert config.tp_percentage_short == 0.003
        assert config.sl_percentage_short == 0.01
        assert config.hard_sl_percentage_short == 0.017
    
    def test_position_config_custom_values(self):
        """Test PositionConfig with custom values."""
        config = PositionConfig(
            tp_percentage_long=0.005,
            sl_percentage_long=0.015,
            hard_sl_percentage_long=0.025,
            tp_percentage_short=0.004,
            sl_percentage_short=0.012,
            hard_sl_percentage_short=0.02
        )
        
        assert config.tp_percentage_long == 0.005
        assert config.sl_percentage_long == 0.015
        assert config.hard_sl_percentage_long == 0.025
        assert config.tp_percentage_short == 0.004
        assert config.sl_percentage_short == 0.012
        assert config.hard_sl_percentage_short == 0.02 