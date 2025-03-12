from globals import set_clean_sell_signal, set_clean_buy_signal

def initial_adjustments(leverage, symbols, client,logger):
    # Her sembol için kaldıracı ayarla
    for symbol in symbols:
        try:
            set_clean_sell_signal(False, symbol)
            set_clean_buy_signal(False, symbol)
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"{symbol} için kaldıraç {leverage}x olarak ayarlandı")
        except Exception as e:
            logger.error(f"{symbol} için kaldıraç ayarlama hatası: {e}")