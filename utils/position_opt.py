def get_entry_price(symbol, client, logger):
    try:
        # Sembol için pozisyon bilgilerini al
        positions = client.futures_position_information(symbol=symbol)
        
        # Pozisyonları kontrol et
        for pos in positions:
            if pos['symbol'] == symbol:
                position_amount = float(pos['positionAmt'])
                entry_price = float(pos['entryPrice'])
                
                if position_amount != 0:  # Pozisyon açıksa
                    logger.info(f"{symbol} için açık pozisyon giriş fiyatı: {entry_price}")
                    return entry_price
                else:
                    logger.info(f"{symbol} için açık pozisyon bulunamadı.")
                    return None

    except Exception as e:
        logger.error(f"{symbol} için giriş fiyatı alınırken hata: {e}")
        return None

# Bakiye bilgisini al
def get_usdt_balance(client, logger):
    try:
        account_info = client.futures_account()
        for asset in account_info['assets']:
            if asset['asset'] == 'USDT':
                return float(asset['availableBalance'])
    except Exception as e:
        logger.error(f"Bakiye alınırken hata: {e}")
        return 0

# Açık pozisyon sayısını al
def get_open_positions_count(client, logger):
    try:
        positions = client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        return len(open_positions)
    except Exception as e:
        logger.error(f"Açık pozisyon sayısı alınırken hata: {e}")
        return 0

# Pozisyon kapandığında açık emirleri iptal et
def cancel_open_orders(symbol, client, logger):
    try:
        open_orders = client.futures_get_open_orders(symbol=symbol)
        if len(open_orders) ==1:
            for order in open_orders:
                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
                logger.info(f"{symbol} için açık emir iptal edildi: {order['orderId']}")
    except Exception as e:
        logger.error(f"{symbol} için açık emirler iptal edilirken hata: {e}")