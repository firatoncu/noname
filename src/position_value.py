from utils.position_opt import get_wallet_balance, check_balance_availability
import asyncio

async def position_val(leverage, capital_tbu, max_positions, logger, client):
    try:
        # Fetch current USDT balance asynchronously
        if capital_tbu != -999:
            check_balance_availability(capital_tbu, client, logger)
            max_position_size = float(capital_tbu) / int(max_positions)
        else:
            max_position_size = get_wallet_balance(client, logger) / int(max_positions)
  
        # Calculate position value
        POSITION_VALUE = (max_position_size-1) * leverage
        return POSITION_VALUE

    except Exception as e:
        logger.error(f"Error in Position Value function : {e}")
        await asyncio.sleep(2)  # Non-blocking sleep
        return 0  # Return a default value on error
  