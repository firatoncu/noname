def adjust_leverage(leverage, symbols, client,logger):
    # Her sembol için kaldıracı ayarla
    for symbol in symbols:
        try:
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info(f"{symbol} için kaldıraç {leverage}x olarak ayarlandı")
        except Exception as e:
            logger.error(f"{symbol} için kaldıraç ayarlama hatası: {e}")