from globals import set_clean_sell_signal, set_clean_buy_signal

async def initial_adjustments(leverage, symbols, client, logger):
    try:
        for symbol in symbols:
            set_clean_sell_signal(False, symbol)
            set_clean_buy_signal(False, symbol)
            await client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except Exception as e:
        logger.error(f"Initial adjustments failed: {e}")