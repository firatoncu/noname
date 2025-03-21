import asyncio
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import pandas as pd
from utils.position_opt import get_open_positions_count, get_entry_price, set_stoploss_price
from src.check_condition import check_buy_conditions, check_sell_conditions
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from src.position_value import position_val
from utils.globals import set_capital_tbu, get_capital_tbu, set_clean_buy_signal, set_clean_sell_signal, get_sl_price
from utils.cursor_movement import logger_move_cursor_up, clean_line
from utils.current_status import current_position_monitor


# Async function to process a single symbol
async def process_symbol(symbol, client, logger, max_open_positions, leverage, stepSizes, quantityPrecisions, pricePrecisions, position_value):
    try:
        # Get last 500 candles
        klines = await client.futures_klines(symbol=symbol, interval='1m', limit=500)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = pd.to_numeric(df['close'])
        close_price = df['close'].iloc[-1]

        # Check buy and sell conditions
        buyAll = check_buy_conditions(df, symbol, logger)
        sellAll = check_sell_conditions(df, symbol, logger)


        # Get current position
        positions = await client.futures_position_information(symbol=symbol)
        current_position = 0.0
        for pos in positions:
            if pos['symbol'] == symbol:
                current_position = float(pos['positionAmt'])
                break


        # Position and order handling
        stepSize = stepSizes[symbol]
        qty_precision = quantityPrecisions[symbol]
        price_precision = pricePrecisions[symbol]
        Q = calculate_quantity(position_value, close_price, stepSize, qty_precision)

        if current_position > 0:
            entry_price = await get_entry_price(symbol, client, logger)
            tp_price = round(entry_price * 1.0033, price_precision)
            sl_price = get_sl_price(symbol)
            #if position is opened manually, sl_price will be 0. In this case, set sl_price to 0.9966 of entry price
            if sl_price == 0:
                sl_price = round(entry_price * 0.9966, price_precision)

            if (close_price <= sl_price or close_price >= tp_price):
                await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
                return
                
        if current_position < 0:
            entry_price = await get_entry_price(symbol, client, logger)
            tp_price = round(entry_price * 0.9966, price_precision)
            sl_price = get_sl_price(symbol)
            #if position is opened manually, sl_price will be 0. In this case, set sl_price to 0.9966 of entry price
            if sl_price == 0:
                sl_price = round(entry_price * 1.0033, price_precision)

            if(close_price >= sl_price or close_price <= tp_price):
                await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=abs(current_position))
                return
            

        open_positions_count = await get_open_positions_count(client, logger)
        # Buy operation
        if buyAll and current_position <= 0 and open_positions_count < max_open_positions:
            
            quantity_to_buy = Q - current_position
            entry_price = await get_entry_price(symbol, client, logger)
            profit_percentage = 0.0
            if current_position < 0:
                profit_percentage = (entry_price - close_price) / entry_price 
                if profit_percentage <= 0.01:  # Close short and open long
                    return
            else:
                quantity_to_buy = Q
           
            if max_open_positions > await get_open_positions_count(client, logger):
                await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity_to_buy)
                set_stoploss_price(buyAll, symbol, df["close"], price_precision, logger)
            # Set Global Variables
            set_clean_buy_signal(False, symbol)


        # Sell operation
        elif sellAll and current_position >= 0 and open_positions_count < max_open_positions:
            
            quantity_to_sell = Q + current_position
            entry_price = await get_entry_price(symbol, client, logger)
            profit_percentage = 0.0
            
            if current_position > 0:  # Close long and open short
                profit_percentage = (close_price- entry_price) / entry_price
                if profit_percentage <= 0.01:
                    return
            else:
                quantity_to_sell = Q

            if max_open_positions > await get_open_positions_count(client, logger):
                await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity_to_sell)
                set_stoploss_price(buyAll, symbol, df["close"], price_precision, logger)
            # Set Global Variables
            set_clean_sell_signal(False, symbol)
            
    except Exception as e:
        logger.error(f"{symbol} işlenirken hata: {e}")

# Main async function
async def open_position(max_open_positions, symbols, logger, client, leverage):
    try:
        # Fetch static data once
        stepSizes, quantityPrecisions, pricePrecisions = await stepsize_precision(client, symbols)
        position_value = await position_val(leverage, get_capital_tbu(), max_open_positions, logger, client)
        all_positions = await client.futures_position_information()
        position_monitor_text = ""
        pos_count = 0
        for p in all_positions:
            if float(p['positionAmt']) == 0:
                continue
            
            position_response = await current_position_monitor(p, pricePrecisions, logger)
            if position_monitor_text == "" and position_response != None:
                position_monitor_text = str(position_response)
            elif position_monitor_text != "" and position_response != None:
                position_monitor_text = str(position_response)  + "\n" + str(position_monitor_text) 

            pos_count = pos_count +1
        if position_monitor_text == "":
            clean_line(pos_count+2)
            print("No Open Positions !")
        else:
            clean_line(pos_count+2)
            print("Open Positions: \n" + position_monitor_text)
        
        logger_move_cursor_up(pos_count+1)

        # Create a list of tasks for each symbol
        tasks = [
            process_symbol(
                symbol, client, logger, max_open_positions, leverage,
                stepSizes, quantityPrecisions, pricePrecisions, position_value
            )
            for symbol in symbols
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Ana döngüde hata: {e}")
        await asyncio.sleep(2)