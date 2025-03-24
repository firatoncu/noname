from utils.globals import set_clean_buy_signal, set_clean_sell_signal
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from src.check_condition import check_buy_conditions, check_sell_conditions

async def check_create_order(symbol, Q, df, client, logger):
    try:
        buyAll = check_buy_conditions(df, symbol, logger)
        sellAll = check_sell_conditions(df, symbol, logger)
        
        if buyAll:
            await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=Q)
            set_clean_buy_signal(False, symbol)

        elif sellAll:
            await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=Q)
            set_clean_sell_signal(False, symbol)

    except Exception as e:
        logger.error(f"Placing Order Error: {e}")
        return