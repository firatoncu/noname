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
    """
    Monitor open positions and execute TP/SL logic.
    
    Args:
        client: Binance client
        pricePrecisions: Price precision mapping
        logger: Logger instance
    """
    try:
        while True:
            try:
                all_positions = await client.futures_position_information()
                
                # Check if there are any open positions
                open_positions = [p for p in all_positions if float(p['positionAmt']) != 0]
                
                if not open_positions:
                    # No open positions, sleep and continue
                    await asyncio.sleep(5)
                    continue
                
                # Monitor each open position
                for position in open_positions:
                    symbol = position['symbol']
                    position_amt = float(position['positionAmt'])
                    
                    if position_amt != 0:  # Only process if there's an actual position
                        await tpsl_checker(symbol, position_amt, pricePrecisions, client, logger)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in position checker loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Critical error in position_checker: {e}")


async def tpsl_checker(symbol, current_position, pricePrecisions, client, logger):
    """
    Check take profit and stop loss conditions for a position.
    
    Args:
        symbol: Trading symbol
        current_position: Current position amount
        pricePrecisions: Price precision mapping
        client: Binance client
        logger: Logger instance
    """
    try:
        df, close_price = await binance_fetch_data(300, symbol, client)
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        histogram = macd.macd_diff()

        buy_hist_check = last500_histogram_check(histogram, "buy", logger, quantile=0.7, histogram_lookback=200)
        sell_hist_check = last500_histogram_check(histogram, "sell", logger, quantile=0.7, histogram_lookback=200)

        # LONG position logic
        if current_position > 0:
            entry_price = await get_entry_price(symbol, client, logger)
            tp_price = round(entry_price * 1.003, pricePrecisions[symbol])  # 0.3% TP
            sl_price = round(entry_price * 0.99, pricePrecisions[symbol])   # 1% SL
            hard_sl_price = round(entry_price * 0.983, pricePrecisions[symbol])  # 1.7% hard SL

            logger.info(f"LONG position monitoring - {symbol}: Entry={entry_price}, Current={close_price}, TP={tp_price}, SL={sl_price}, Hard SL={hard_sl_price}")
            
            # Check exit conditions
            should_close = False
            is_take_profit = False
            
            if close_price >= tp_price:
                should_close = True
                is_take_profit = True
                logger.info(f"Take profit triggered for LONG {symbol}")
            elif close_price <= hard_sl_price:
                should_close = True
                is_take_profit = False
                logger.info(f"Hard stop loss triggered for LONG {symbol}")
            elif close_price <= sl_price and sell_hist_check:
                should_close = True
                is_take_profit = False
                logger.info(f"Stop loss + histogram confirmation triggered for LONG {symbol}")
            
            if should_close:
                try:
                    # Close the position
                    await client.futures_create_order(
                        symbol=symbol, 
                        side=SIDE_SELL, 
                        type=ORDER_TYPE_MARKET, 
                        quantity=abs(current_position)
                    )
                    logger.info(f"Successfully closed LONG position for {symbol}")
                    
                    # Try to cancel any existing limit orders
                    try:
                        limit_order = get_limit_order(symbol)
                        if limit_order and limit_order != "False" and isinstance(limit_order, dict):
                            await client.futures_cancel_order(symbol=symbol, orderId=limit_order['orderId'])
                            logger.info(f"Cancelled limit order for {symbol}")
                    except Exception as e:
                        logger.warning(f"Could not cancel limit order for {symbol}: {e}")
                    
                    # Send notification
                    if get_notif_status():
                        try:
                            if is_take_profit:
                                set_error_counter(0)
                                profit = round(abs(current_position) * (close_price - entry_price), 2)
                                await send_position_close_alert(True, symbol, "LONG", profit)
                                logger.info(f"✅ Take profit notification sent for {symbol}: +${profit}")
                            else:
                                set_error_counter(get_error_counter() + 1)
                                loss = round(abs(current_position) * (entry_price - close_price), 2)
                                await send_position_close_alert(False, symbol, "LONG", loss)
                                logger.info(f"⚠️ Stop loss notification sent for {symbol}: -${loss}")
                        except Exception as e:
                            logger.error(f"Failed to send position close notification for {symbol}: {e}")
                    else:
                        logger.info(f"Notifications disabled - position closed for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Failed to close LONG position for {symbol}: {e}")
                    
        # SHORT position logic
        elif current_position < 0:
            entry_price = await get_entry_price(symbol, client, logger)
            tp_price = round(entry_price * 0.997, pricePrecisions[symbol])   # 0.3% TP
            sl_price = round(entry_price * 1.01, pricePrecisions[symbol])    # 1% SL
            hard_sl_price = round(entry_price * 1.017, pricePrecisions[symbol])  # 1.7% hard SL

            logger.info(f"SHORT position monitoring - {symbol}: Entry={entry_price}, Current={close_price}, TP={tp_price}, SL={sl_price}, Hard SL={hard_sl_price}")
            
            # Check exit conditions
            should_close = False
            is_take_profit = False
            
            if close_price <= tp_price:
                should_close = True
                is_take_profit = True
                logger.info(f"Take profit triggered for SHORT {symbol}")
            elif close_price >= hard_sl_price:
                should_close = True
                is_take_profit = False
                logger.info(f"Hard stop loss triggered for SHORT {symbol}")
            elif close_price >= sl_price and buy_hist_check:
                should_close = True
                is_take_profit = False
                logger.info(f"Stop loss + histogram confirmation triggered for SHORT {symbol}")
            
            if should_close:
                try:
                    # Close the position
                    await client.futures_create_order(
                        symbol=symbol, 
                        side=SIDE_BUY, 
                        type=ORDER_TYPE_MARKET, 
                        quantity=abs(current_position)
                    )
                    logger.info(f"Successfully closed SHORT position for {symbol}")
                    
                    # Try to cancel any existing limit orders
                    try:
                        limit_order = get_limit_order(symbol)
                        if limit_order and limit_order != "False" and isinstance(limit_order, dict):
                            await client.futures_cancel_order(symbol=symbol, orderId=limit_order['orderId'])
                            logger.info(f"Cancelled limit order for {symbol}")
                    except Exception as e:
                        logger.warning(f"Could not cancel limit order for {symbol}: {e}")
                    
                    # Send notification
                    if get_notif_status():
                        try:
                            if is_take_profit:
                                set_error_counter(0)
                                profit = round(abs(current_position) * (entry_price - close_price), 2)
                                await send_position_close_alert(True, symbol, "SHORT", profit)
                                logger.info(f"✅ Take profit notification sent for {symbol}: +${profit}")
                            else:
                                set_error_counter(get_error_counter() + 1)
                                loss = round(abs(current_position) * (close_price - entry_price), 2)
                                await send_position_close_alert(False, symbol, "SHORT", loss)
                                logger.info(f"⚠️ Stop loss notification sent for {symbol}: -${loss}")
                        except Exception as e:
                            logger.error(f"Failed to send position close notification for {symbol}: {e}")
                    else:
                        logger.info(f"Notifications disabled - position closed for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Failed to close SHORT position for {symbol}: {e}")
                    
    except Exception as e:
        logger.error(f"Error in tpsl_checker for {symbol}: {e}")


# Commented out limit order monitoring - can be enabled if needed
"""
async def check_limit_orders(client, logger):
    '''Monitor and handle limit order fills.'''
    try:
        # Get all symbols with active limit orders
        symbols_with_orders = []  # This would need to be populated from your state
        
        for symbol in symbols_with_orders:
            if get_order_status(symbol) == "LONG" and get_limit_order(symbol) != "False":
                limit_order = get_limit_order(symbol)
                order_status = await client.futures_get_order(symbol=symbol, orderId=limit_order['orderId'])
                if order_status['status'] == 'FILLED':
                    set_error_counter(0)
                    set_order_status("False", symbol)
                    set_limit_order("False", symbol)    
                    if get_notif_status():
                        await send_tp_limit_filled_alert(symbol, "LONG")

            if get_order_status(symbol) == "SHORT" and get_limit_order(symbol) != "False":
                limit_order = get_limit_order(symbol)
                order_status = await client.futures_get_order(symbol=symbol, orderId=limit_order['orderId'])
                if order_status['status'] == 'FILLED':
                    set_error_counter(0)
                    set_order_status("False", symbol)
                    set_limit_order("False", symbol)
                    if get_notif_status():
                        await send_tp_limit_filled_alert(symbol, "SHORT")
                        
    except Exception as e:
        logger.error(f"Error checking limit orders: {e}")
"""