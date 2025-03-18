from utils.position_opt import get_usdt_balance

import asyncio

async def position_val(leverage, capital_tbu, max_positions, logger, client):
    try:
        # Fetch current USDT balance asynchronously
        if capital_tbu != -999:
            usdt_balance = capital_tbu / max_positions
        else:
            usdt_balance = round(await get_usdt_balance(client, logger) / max_positions) - 1
        if (max_positions < 2 and usdt_balance + 20 <= 0) or (max_positions >= 2 and usdt_balance <= 50):
            logger.error("USDT bakiyesi yetersiz, işlem yapılamıyor")
            await asyncio.sleep(600)  # Non-blocking sleep
            return 0  # Return early to avoid further processing

        # Calculate position value
        POSITION_VALUE = usdt_balance * leverage

        return POSITION_VALUE

    except Exception as e:
        logger.error(f"Position Value fonksiyonunda hata: {e}")
        await asyncio.sleep(2)  # Non-blocking sleep
        return 0  # Return a default value on error
    