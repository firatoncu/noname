import asyncio
from binance import AsyncClient  # Use the async client from binance-connector
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import pandas as pd
from utils.position_opt import cancel_open_orders, get_open_positions_count, get_entry_price
from src.check_condition import check_buy_conditions, check_sell_conditions
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from src.position_value import position_val
from utils.globals import set_capital_tbu, get_capital_tbu, set_clean_buy_signal, set_clean_sell_signal, set_last_position_qty, set_tp_price, set_sl_price, get_tp_price, get_sl_price, set_side_info, get_side_info, get_last_position_qty
from utils.cursor_movement import logger_move_cursor_up
from colorama import init, Fore, Style

init()

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

        # Get open positions count
        open_positions_count = await get_open_positions_count(client, logger)

        # Cancel open orders if position is closed
        if current_position == 0:
            await cancel_open_orders(symbol, client, logger)

        # Position and order handling
        stepSize = stepSizes[symbol]
        qty_precision = quantityPrecisions[symbol]
        price_precision = pricePrecisions[symbol]
        Q = calculate_quantity(position_value, close_price, stepSize, qty_precision)

        if current_position != 0:
            if get_side_info(symbol) == 'LONG':
                sl_price = get_sl_price(symbol)
                tp_price = get_tp_price(symbol)
                if (close_price <= sl_price or close_price >= tp_price):
                    last_position_qty = get_last_position_qty(symbol)
                    await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=last_position_qty)
                    set_clean_buy_signal(False, symbol)
                    set_side_info('', symbol)
                    return
                
            if get_side_info(symbol) == 'SHORT':
                sl_price = get_sl_price(symbol)
                tp_price = get_tp_price(symbol)
                if(close_price >= sl_price or close_price <= tp_price):
                    last_position_qty = get_last_position_qty(symbol)
                    await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=last_position_qty)
                    set_clean_sell_signal(False, symbol)
                    set_side_info('', symbol)
                    return

        # Buy operation
        if buyAll and current_position <= 0 and open_positions_count < max_open_positions:
            if current_position < 0:  # Close short and open long
                quantity_to_buy = Q - current_position
                entry_price = await get_entry_price(symbol, client, logger)
                profit_percentage = (close_price - entry_price) / entry_price
                if profit_percentage <= 0.01:
                    return
            else:
                quantity_to_buy = Q
            logger.info(f"{symbol} için UZUN pozisyon açılıyor, miktar: {quantity_to_buy}")
            logger_move_cursor_up()
            await client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity_to_buy)

            # Set Global Variables
            set_last_position_qty(quantity_to_buy, symbol)
            set_clean_buy_signal(False, symbol)
            set_tp_price(round(close_price * 1.0033, price_precision), symbol)  # 0.5% profit
            set_sl_price(round(close_price * 0.993, price_precision), symbol)   # 1.5% loss
            set_side_info('LONG', symbol)
            set_capital_tbu(get_capital_tbu() + profit_percentage) 

            logger.info(f"{symbol} - Opened LONG - Quantity: {quantity_to_buy}, TP Price: {tp_price}, SL Price: {sl_price}")
            logger_move_cursor_up()

        # Sell operation
        elif sellAll and current_position >= 0 and open_positions_count < max_open_positions:
            if current_position > 0:  # Close long and open short
                quantity_to_sell = Q + current_position
                entry_price = await get_entry_price(symbol, client, logger)
                profit_percentage = (entry_price - close_price) / entry_price
                if profit_percentage <= 0.01:
                    return
            else:
                quantity_to_sell = Q
            logger.info(f"{symbol} için KISA pozisyon açılıyor, miktar: {quantity_to_sell}")
            logger_move_cursor_up()
            await client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity_to_sell)

            # Set Global Variables
            set_clean_sell_signal(False, symbol)
            set_last_position_qty(quantity_to_sell, symbol)
            set_tp_price(round(close_price * 0.9966, price_precision), symbol)
            set_sl_price(round(close_price * 1.007, price_precision), symbol)
            set_side_info('SHORT', symbol)
            set_capital_tbu(get_capital_tbu() - profit_percentage) 

            logger.info(f"{symbol} - Opened SHORT - Quantity: {quantity_to_sell}, TP Price: {tp_price}, SL Price: {sl_price}")
            logger_move_cursor_up()

    except Exception as e:
        logger.error(f"{symbol} işlenirken hata: {e}")
        logger_move_cursor_up()

# Main async function
async def open_position(max_open_positions, symbols, logger, client, leverage):
    try:
        # Fetch static data once
        stepSizes, quantityPrecisions, pricePrecisions = await stepsize_precision(client, symbols)
        position_value = await position_val(leverage, get_capital_tbu(), max_open_positions, logger, client)
        all_positions = await client.futures_position_information()
        print(" | ".join([f"{p['symbol']}: Size=${round(float(p['notional']),2)}, {Fore.GREEN if float(p['unRealizedProfit']) > 0 else Fore.RED}P&L=${float(p['unRealizedProfit']):.2f}{Style.RESET_ALL}" for p in all_positions if float(p['positionAmt']) != 0]) or "No open positions!           ")
        logger_move_cursor_up()
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