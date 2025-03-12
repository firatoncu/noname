from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET 
import time
from utils.position_opt import cancel_open_orders, get_open_positions_count, get_entry_price
from src.check_condition import check_buy_conditions, check_sell_conditions
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from utils.position_opt import get_open_positions_count
from src.position_value import position_val
import pandas as pd 

def open_position(max_open_positions, symbols, logger, 
                  client, leverage):
    try:
        for symbol in symbols:
            try:
                # Son 201 mumu al
                klines = client.futures_klines(symbol=symbol, interval='1m', limit=500)
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
                df['close'] = pd.to_numeric(df['close'])
                close_price = df['close'].iloc[-1]

                # Alış ve satış koşullarını kontrol et
                buyAll = check_buy_conditions(df,  logger)
                sellAll = check_sell_conditions(df, logger)

                # Mevcut pozisyonu al
                positions = client.futures_position_information(symbol=symbol)
                current_position = 0.0
                for pos in positions:
                    if pos['symbol'] == symbol:
                        current_position = float(pos['positionAmt'])
                        break
                
                open_positions_count = get_open_positions_count(client, logger)

                stepSizes, quantityPrecisions, pricePrecisions = stepsize_precision(client, symbols)
                position_value = position_val(leverage, logger, client)


                # Pozisyon kapandığında açık emirleri iptal et
                if current_position == 0:
                    cancel_open_orders(symbol, client, logger)

                # Pozisyon ve emir kontrolü
                stepSize = stepSizes[symbol]
                qty_precision = quantityPrecisions[symbol]
                price_precision = pricePrecisions[symbol]
                Q = calculate_quantity(position_value, close_price, stepSize, qty_precision)

                # Alış işlemi
                if buyAll and current_position <= 0 and open_positions_count < max_open_positions:
                    if current_position < 0:  # Kısa pozisyonu kapat ve uzun aç
                        quantity_to_buy = Q - current_position
                        entry_price = get_entry_price(symbol,client,logger)
                        profit_percentage = (close_price - entry_price) / entry_price
                        if profit_percentage <= 0.01:
                            break
                    else:
                        quantity_to_buy = Q
                    logger.info(f"{symbol} için UZUN pozisyon açılıyor, miktar: {quantity_to_buy}")
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity_to_buy)
                    entry_price = close_price
                    tp_price = round(entry_price * 1.0033, price_precision)  # %0.5 kâr
                    sl_price = round(entry_price * 0.993, price_precision)  # %1.5 zarar
                    logger.info(f"{symbol} - UZUN - Miktar: {quantity_to_buy}, TP: {tp_price}, SL: {sl_price}")
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type='TAKE_PROFIT_MARKET', stopPrice=tp_price, closePosition=True)
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type='STOP_MARKET', stopPrice=sl_price, closePosition=True)
                    logger.info(f"{symbol} için UZUN pozisyon açıldı")

                # Satış işlemi
                elif sellAll and current_position >= 0 and open_positions_count < max_open_positions:
                    if current_position > 0:  # Uzun pozisyonu kapat ve kısa aç
                        quantity_to_sell = Q + current_position
                        entry_price = get_entry_price(symbol, client, logger)
                        profit_percentage = (entry_price - close_price) / entry_price
                        if profit_percentage <= 0.01:
                            break
                    else:
                        quantity_to_sell = Q
                    logger.info(f"{symbol} için KISA pozisyon açılıyor, miktar: {quantity_to_sell}")
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity_to_sell)
                    entry_price = close_price
                    tp_price = round(entry_price * 0.9966, price_precision)  # %0.5 kâr
                    sl_price = round(entry_price * 1.007, price_precision)  # %1.5 zarar
                    logger.info(f"{symbol} - KISA - Miktar: {quantity_to_sell}, TP: {tp_price}, SL: {sl_price}")
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type='TAKE_PROFIT_MARKET', stopPrice=tp_price, closePosition=True)
                    client.futures_create_order(symbol=symbol, side=SIDE_BUY, type='STOP_MARKET', stopPrice=sl_price, closePosition=True)
                    logger.info(f"{symbol} için KISA pozisyon açıldı")

            except Exception as e:
                logger.error(f"{symbol} işlenirken hata: {e}")

        # 2 saniye bekle
        time.sleep(2)

    except Exception as e:
        logger.error(f"Ana döngüde hata: {e}")
        time.sleep(2)