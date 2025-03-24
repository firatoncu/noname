from utils.current_status import current_position_monitor, status_printer
from utils.position_opt import get_entry_price
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from utils.globals import set_error_counter, get_error_counter
from utils.fetch_data import binance_fetch_data
from src.indicators import last500_histogram_check
import ta
import asyncio

async def position_checker(client, pricePrecisions, logger):

        while await client.futures_position_information():     
            all_positions = await client.futures_position_information()
            p = all_positions[0]
            position_response = await current_position_monitor(p, pricePrecisions, logger)
            status_printer(True, position_response)
            await tpsl_checker(p['symbol'], float(p['positionAmt']), pricePrecisions, client, logger)
            await asyncio.sleep(1)
        
        status_printer(False, None)



async def tpsl_checker(symbol, current_position, pricePrecisions, client, logger):
    df, close_price = await binance_fetch_data(300, symbol, client)
    macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    histogram = macd.macd_diff()

    buy_hist_check = last500_histogram_check(histogram, "buy", logger, quantile=0.7, histogram_lookback=200)
    sell_hist_check = last500_histogram_check(histogram, "sell", logger, quantile=0.7, histogram_lookback=200)

    if current_position > 0:
        entry_price = await get_entry_price(symbol, client, logger)
        tp_price = round(entry_price * 1.0033, pricePrecisions) # %1
        sl_price = round(entry_price * 0.99, pricePrecisions) # %3
        hard_sl_price = round(entry_price * 0.983, pricePrecisions) # %5

        if ((close_price >= tp_price) or (close_price <= sl_price and sell_hist_check == True) or (close_price <= hard_sl_price)): 
            await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
            if close_price >= tp_price:
                set_error_counter(0)
            else:
                set_error_counter(get_error_counter() + 1)
            return
            
    if current_position < 0:
        entry_price = await get_entry_price(symbol, client, logger)
        tp_price = round(entry_price * 0.9966, pricePrecisions) # %1
        sl_price = round(entry_price * 1.01, pricePrecisions) # %3
        hard_sl_price = round(entry_price * 1.017, pricePrecisions) # %5

        if ((close_price <= tp_price) or (close_price >= sl_price and buy_hist_check == True) or (close_price >= hard_sl_price)):
            await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
            if close_price <= tp_price:
                set_error_counter(0)
            else:
                set_error_counter(get_error_counter() + 1)
            return