from utils.globals import set_clean_buy_signal, set_clean_sell_signal
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from src.check_condition import check_buy_conditions, check_sell_conditions
from utils.send_notification import send_position_open_alert

async def check_create_order(symbol, Q, df, client, logger):
    try:
        buyAll = await check_buy_conditions(500, symbol, client, logger)
        sellAll = await check_sell_conditions(500, symbol, client, logger)
        
        if buyAll:
            await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=Q)
            set_clean_buy_signal(0, symbol)
            #await send_position_open_alert(symbol)

        elif sellAll:
            await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=Q)
            set_clean_sell_signal(0, symbol)
            #await send_position_open_alert(symbol)

    except Exception as e:
        logger.error(f"Placing Order Error: {e}")
        return