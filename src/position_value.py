from utils.position_opt import get_open_positions_count, get_usdt_balance

import asyncio

async def position_val(leverage, logger, client):
    try:
        # Fetch current USDT balance asynchronously
        usdt_balance = round(await get_usdt_balance(client, logger)) - 20
        if usdt_balance + 20 <= 0:
            logger.warning("USDT bakiyesi yetersiz, işlem yapılamıyor")
            await asyncio.sleep(60)  # Non-blocking sleep
            return 0  # Return early to avoid further processing

        # Fetch open positions count asynchronously
        open_positions_count = await get_open_positions_count(client, logger)
        
        # Calculate margin per position
        if open_positions_count == 1:
            margin_per_position = round(usdt_balance) - 1
        else:
            margin_per_position = round(usdt_balance / 2) - 1
        
        # Calculate position value
        POSITION_VALUE = margin_per_position * leverage

        return POSITION_VALUE

    except Exception as e:
        logger.error(f"Position Value fonksiyonunda hata: {e}")
        await asyncio.sleep(2)  # Non-blocking sleep
        return 0  # Return a default value on error
    