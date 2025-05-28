from utils.position_opt import get_wallet_balance
from utils.margin_selector import MarginSelector
import asyncio

async def position_val(leverage, capital_tbu, max_positions, logger, client, config=None):
    """
    Calculate position value based on margin selection.
    
    Args:
        leverage: Trading leverage
        capital_tbu: Capital to be used (legacy parameter)
        max_positions: Maximum number of positions
        logger: Logger instance
        client: Binance client
        config: Configuration dictionary for margin selection
        
    Returns:
        Position value for each trade
    """
    try:
        # If config is provided and margin selection is enabled, use new margin selector
        if config and config.get('trading', {}).get('margin', {}).get('ask_user_selection', False):
            logger.info("Using margin selector for position value calculation")
            
            # Initialize margin selector
            margin_selector = MarginSelector(config, logger)
            
            # Select margin
            margin_mode, margin_amount = await margin_selector.select_margin(client)
            
            # Calculate position value using selected margin
            position_value = margin_selector.calculate_position_value(
                margin_amount, leverage, max_positions
            )
            
            logger.info(
                f"Position value calculated using margin selector: {position_value:.2f} USDT",
                extra={
                    "margin_mode": margin_mode,
                    "margin_amount": margin_amount,
                    "leverage": leverage,
                    "max_positions": max_positions
                }
            )
            
            return position_value
            
        else:
            # Legacy calculation method
            logger.info("Using legacy position value calculation")
            
            # Fetch current USDT balance asynchronously
            if capital_tbu != -999:
                max_position_size = float(capital_tbu) - 3 / int(max_positions)
            else:
                max_position_size = (await get_wallet_balance(client, logger)) / int(max_positions)
      
            # Calculate position value
            POSITION_VALUE = (max_position_size-1) * leverage
            
            logger.info(
                f"Position value calculated using legacy method: {POSITION_VALUE:.2f} USDT",
                extra={
                    "max_position_size": max_position_size,
                    "leverage": leverage,
                    "capital_tbu": capital_tbu
                }
            )
            
            return POSITION_VALUE

    except Exception as e:
        logger.error(f"Error in Position Value function : {e}")
        await asyncio.sleep(2)  # Non-blocking sleep
        return 0  # Return a default value on error


# Backward compatibility function
async def position_val_legacy(leverage, capital_tbu, max_positions, logger, client):
    """
    Legacy position value calculation for backward compatibility.
    
    Args:
        leverage: Trading leverage
        capital_tbu: Capital to be used
        max_positions: Maximum number of positions
        logger: Logger instance
        client: Binance client
        
    Returns:
        Position value for each trade
    """
    return await position_val(leverage, capital_tbu, max_positions, logger, client, config=None)
  