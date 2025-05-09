from utils.current_status import current_position_monitor, status_printer
from utils.position_opt import get_entry_price
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from utils.globals import set_error_counter, get_error_counter, get_notif_status, set_order_status, get_order_status, set_limit_order, get_limit_order
from utils.fetch_data import binance_fetch_data
from utils.send_notification import send_position_close_alert, send_tp_limit_filled_alert
from src.indicators.macd_fibonacci import last500_histogram_check
import ta
import asyncio


async def position_checker(client, pricePrecisions, logger):

        while await client.futures_position_information():     
            all_positions = await client.futures_position_information()
            p = all_positions[0]
            #position_response = await current_position_monitor(p, pricePrecisions, logger)
            #status_printer(True, position_response)
            await tpsl_checker(p['symbol'], float(p['positionAmt']), pricePrecisions, client, logger)
            await asyncio.sleep(1)
        
        #status_printer(False, None)

async def tpsl_checker(symbol, current_position, pricePrecisions, client, logger):
    df, close_price = await binance_fetch_data(300, symbol, client)
    macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    histogram = macd.macd_diff()

    buy_hist_check = last500_histogram_check(histogram, "buy", logger, quantile=0.7, histogram_lookback=200)
    sell_hist_check = last500_histogram_check(histogram, "sell", logger, quantile=0.7, histogram_lookback=200)



    if current_position > 0:
        entry_price = await get_entry_price(symbol, client, logger)
        tp_price = round(entry_price * 1.003, pricePrecisions[symbol]) # %1.5
        sl_price = round(entry_price * 0.99, pricePrecisions[symbol]) # %5
        hard_sl_price = round(entry_price * 0.983, pricePrecisions[symbol]) # 8.5

                
        # If limit order wasn't placed or filled, proceed with the regular TP/SL logic
        if ((close_price >= tp_price) or (close_price <= sl_price and sell_hist_check == True) or (close_price <= hard_sl_price)):
            await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
            limit_order = get_limit_order(symbol)
            await client.futures_cancel_order(symbol=symbol, orderId=limit_order['orderId'])
            if close_price >= tp_price:
                set_error_counter(0)
                if get_notif_status() == True:
                    profit = round(abs(current_position) * (close_price - entry_price), 2)
                    await send_position_close_alert(True, symbol, "LONG", profit)
            else:
                set_error_counter(get_error_counter() + 1)
                if get_notif_status() == True:
                    loss = round(abs(current_position) * (entry_price - close_price), 2)
                    await send_position_close_alert(False, symbol, "LONG", loss)
            return
            
    if current_position < 0:
        entry_price = await get_entry_price(symbol, client, logger)
        tp_price = round(entry_price * 0.997, pricePrecisions[symbol]) # %1.5
        sl_price = round(entry_price * 1.01, pricePrecisions[symbol]) # %5
        hard_sl_price = round(entry_price * 1.017, pricePrecisions[symbol]) # %8.5


        if ((close_price <= tp_price) or (close_price >= sl_price and buy_hist_check == True) or (close_price >= hard_sl_price)):
            await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
            limit_order = get_limit_order(symbol)
            await client.futures_cancel_order(symbol=symbol, orderId=limit_order['orderId'])
            if close_price <= tp_price:
                set_error_counter(0)
                if get_notif_status() == True:
                    profit = round(abs(current_position) * (entry_price - close_price), 2)
                    await send_position_close_alert(True, symbol, "SHORT", profit)
            else:
                set_error_counter(get_error_counter() + 1)
                if get_notif_status() == True:
                    loss = round(abs(current_position) * (close_price - entry_price), 2)
                    await send_position_close_alert(False, symbol, "SHORT", loss)
            return
        


""" if get_order_status(symbol) == "LONG" and get_limit_order(symbol) != "False":
        limit_order = get_limit_order(symbol)
        order_status = await client.futures_get_order(symbol=symbol, orderId=limit_order['orderId'])
        if order_status['status'] == 'FILLED':
            set_error_counter(0)
            set_order_status("False", symbol)
            set_limit_order("False", symbol)    
            if get_notif_status() == True:
                await send_tp_limit_filled_alert(symbol, "LONG")
            return

    if get_order_status(symbol) == "SHORT" and get_limit_order(symbol) != "False":
        limit_order = get_limit_order(symbol)
        order_status = await client.futures_get_order(symbol=symbol, orderId=limit_order['orderId'])
        if order_status['status'] == 'FILLED':
            set_error_counter(0)
            set_order_status("False", symbol)
            set_limit_order("False", symbol)
            if get_notif_status() == True:
                await send_tp_limit_filled_alert(symbol, "SHORT")
            return """