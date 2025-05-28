"""
Margin Selection Utility

This module provides functionality for selecting margin amounts for trading positions.
It supports different margin modes including fixed amounts, full margin, and percentage-based selection.
"""

import asyncio
import sys
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

# Handle import path for direct execution
if __name__ == "__main__":
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from utils.enhanced_logging import get_logger, LogSeverity, ErrorCategory


class MarginSelector:
    """
    Handles margin selection for trading positions.
    
    Supports multiple margin modes:
    - Fixed: Use a specific margin amount
    - Full: Use all available margin
    - Percentage: Use a percentage of available margin
    """
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize the margin selector.
        
        Args:
            config: Configuration dictionary containing margin settings
            logger: Logger instance for logging operations
        """
        self.config = config
        self.logger = logger or get_logger(__name__)
        self.margin_config = config.get('trading', {}).get('margin', {})
        
    async def get_available_margin(self, client) -> float:
        """
        Get available margin from the trading account.
        
        Args:
            client: Binance client for API operations
            
        Returns:
            Available margin amount in USDT
        """
        try:
            account_info = await client.futures_account()
            available_balance = float(account_info.get('availableBalance', 0))
            
            self.logger.info(
                f"Available margin retrieved: {available_balance} USDT",
                extra={"available_margin": available_balance}
            )
            
            return available_balance
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve available margin",
                category=ErrorCategory.API,
                severity=LogSeverity.HIGH,
                extra={"error": str(e)}
            )
            return 0.0
    
    async def ask_user_for_margin_selection(self, available_margin: float) -> Tuple[str, float]:
        """
        Ask user to select margin mode and amount.
        
        Args:
            available_margin: Available margin amount
            
        Returns:
            Tuple of (selected_mode, selected_amount)
        """
        timeout = self.margin_config.get('user_response_timeout', 30)
        default_to_full = self.margin_config.get('default_to_full_margin', True)
        
        print("\n" + "="*60)
        print("🔹 MARGIN SELECTION")
        print("="*60)
        print(f"Available Margin: {available_margin:.2f} USDT")
        print("\nPlease select your margin mode:")
        print("1. Fixed Amount - Use a specific margin amount")
        print("2. Full Margin - Use all available margin")
        print("3. Percentage - Use a percentage of available margin")
        print(f"\nYou have {timeout} seconds to respond...")
        print("Press Enter after making your selection.")
        
        try:
            # Create a task for user input with timeout
            user_input_task = asyncio.create_task(self._get_user_input())
            
            try:
                selection = await asyncio.wait_for(user_input_task, timeout=timeout)
                return await self._process_user_selection(selection, available_margin)
                
            except asyncio.TimeoutError:
                print(f"\n⏰ Timeout reached ({timeout}s)")
                if default_to_full:
                    print("🔄 Defaulting to full margin as configured")
                    return "full", available_margin
                else:
                    print("🔄 Defaulting to fixed margin as configured")
                    fixed_amount = self.margin_config.get('fixed_amount', 100.0)
                    return "fixed", min(fixed_amount, available_margin)
                    
        except Exception as e:
            self.logger.error(
                "Error during user margin selection",
                extra={"error": str(e)}
            )
            # Fallback to configuration defaults
            return await self._get_default_margin_selection(available_margin)
    
    async def _get_user_input(self) -> str:
        """Get user input asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, "\nEnter your choice (1-3): ")
    
    async def _process_user_selection(self, selection: str, available_margin: float) -> Tuple[str, float]:
        """
        Process user's margin selection.
        
        Args:
            selection: User's input selection
            available_margin: Available margin amount
            
        Returns:
            Tuple of (selected_mode, selected_amount)
        """
        selection = selection.strip()
        
        if selection == "1":
            # Fixed amount
            print("\n📊 Fixed Amount Selected")
            amount_input = input(f"Enter margin amount (max {available_margin:.2f} USDT): ")
            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("❌ Invalid amount. Using default fixed amount.")
                    amount = self.margin_config.get('fixed_amount', 100.0)
                elif amount > available_margin:
                    print(f"❌ Amount exceeds available margin. Using maximum: {available_margin:.2f}")
                    amount = available_margin
                
                print(f"✅ Using fixed margin: {amount:.2f} USDT")
                return "fixed", amount
                
            except ValueError:
                print("❌ Invalid input. Using default fixed amount.")
                amount = min(self.margin_config.get('fixed_amount', 100.0), available_margin)
                return "fixed", amount
                
        elif selection == "2":
            # Full margin
            print(f"\n💰 Full Margin Selected: {available_margin:.2f} USDT")
            return "full", available_margin
            
        elif selection == "3":
            # Percentage
            print("\n📈 Percentage Selected")
            percentage_input = input("Enter percentage (1-100): ")
            try:
                percentage = float(percentage_input)
                if percentage <= 0 or percentage > 100:
                    print("❌ Invalid percentage. Using default 50%.")
                    percentage = 50.0
                
                amount = (percentage / 100) * available_margin
                print(f"✅ Using {percentage}% of margin: {amount:.2f} USDT")
                return "percentage", amount
                
            except ValueError:
                print("❌ Invalid input. Using default 50%.")
                amount = 0.5 * available_margin
                return "percentage", amount
                
        else:
            print("❌ Invalid selection. Defaulting to full margin.")
            return "full", available_margin
    
    async def _get_default_margin_selection(self, available_margin: float) -> Tuple[str, float]:
        """
        Get default margin selection from configuration.
        
        Args:
            available_margin: Available margin amount
            
        Returns:
            Tuple of (selected_mode, selected_amount)
        """
        mode = self.margin_config.get('mode', 'fixed')
        
        if mode == "full":
            return "full", available_margin
        elif mode == "percentage":
            percentage = self.margin_config.get('percentage', 50.0)
            amount = (percentage / 100) * available_margin
            return "percentage", amount
        else:  # fixed
            fixed_amount = self.margin_config.get('fixed_amount', 100.0)
            amount = min(fixed_amount, available_margin)
            return "fixed", amount
    
    async def select_margin(self, client) -> Tuple[str, float]:
        """
        Main method to select margin based on configuration and user input.
        
        Args:
            client: Binance client for API operations
            
        Returns:
            Tuple of (selected_mode, selected_amount)
        """
        try:
            # Get available margin
            available_margin = await self.get_available_margin(client)
            
            if available_margin <= 0:
                self.logger.warning("No available margin found")
                return "fixed", 0.0
            
            # Check if user selection is enabled
            ask_user = self.margin_config.get('ask_user_selection', False)
            
            if ask_user:
                mode, amount = await self.ask_user_for_margin_selection(available_margin)
            else:
                mode, amount = await self._get_default_margin_selection(available_margin)
            
            self.logger.info(
                f"Margin selected: {mode} mode, {amount:.2f} USDT",
                extra={
                    "margin_mode": mode,
                    "margin_amount": amount,
                    "available_margin": available_margin
                }
            )
            
            return mode, amount
            
        except Exception as e:
            self.logger.error(
                "Error in margin selection",
                category=ErrorCategory.TRADING,
                severity=LogSeverity.HIGH,
                extra={"error": str(e)}
            )
            # Return safe defaults
            return "fixed", 100.0
    
    def calculate_position_value(self, margin_amount: float, leverage: int, max_positions: int) -> float:
        """
        Calculate position value based on selected margin.
        
        Args:
            margin_amount: Selected margin amount
            leverage: Trading leverage
            max_positions: Maximum number of positions
            
        Returns:
            Position value for each trade
        """
        try:
            # Calculate margin per position
            margin_per_position = margin_amount / max_positions
            
            # Apply leverage to get position value
            position_value = margin_per_position * leverage
            
            self.logger.info(
                f"Position value calculated: {position_value:.2f} USDT",
                extra={
                    "margin_amount": margin_amount,
                    "margin_per_position": margin_per_position,
                    "leverage": leverage,
                    "max_positions": max_positions,
                    "position_value": position_value
                }
            )
            
            return position_value
            
        except Exception as e:
            self.logger.error(
                "Error calculating position value",
                extra={"error": str(e)}
            )
            return 0.0


# Convenience function for easy usage
async def select_trading_margin(config: Dict[str, Any], client, logger=None) -> Tuple[str, float]:
    """
    Convenience function to select trading margin.
    
    Args:
        config: Configuration dictionary
        client: Binance client
        logger: Logger instance
        
    Returns:
        Tuple of (selected_mode, selected_amount)
    """
    selector = MarginSelector(config, logger)
    return await selector.select_margin(client)


# Test functionality when run directly
if __name__ == "__main__":
    print("🔹 Margin Selector - Direct Test")
    print("=" * 40)
    
    # Mock client for testing
    class MockClient:
        async def futures_account(self):
            return {'availableBalance': '1000.0'}
    
    # Test configuration
    test_config = {
        'trading': {
            'margin': {
                'mode': 'fixed',
                'fixed_amount': 200.0,
                'percentage': 50.0,
                'ask_user_selection': False,
                'default_to_full_margin': True,
                'user_response_timeout': 30
            }
        }
    }
    
    async def test():
        logger = get_logger(__name__)
        client = MockClient()
        selector = MarginSelector(test_config, logger)
        
        print("Testing margin selection...")
        mode, amount = await selector.select_margin(client)
        print(f"Result: {mode} mode, {amount:.2f} USDT")
        
        print("\nTesting position value calculation...")
        position_value = selector.calculate_position_value(amount, 3, 5)
        print(f"Position value: {position_value:.2f} USDT")
    
    try:
        asyncio.run(test())
        print("\n✅ Direct test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}") 