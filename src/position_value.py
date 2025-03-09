import time
from utils.position_opt import get_open_positions_count, get_usdt_balance

def position_val( leverage, logger, client):
    try:    
        # Güncel bakiyeyi al
        usdt_balance = round(get_usdt_balance(client, logger))-20
        if usdt_balance + 20 <= 0:
            logger.warning("USDT bakiyesi yetersiz, işlem yapılamıyor")
            time.sleep(60)
        open_positions_count = get_open_positions_count(client, logger)
        if open_positions_count == 1:
            margin_per_position = round(usdt_balance)-1
        else:
            margin_per_position = round(usdt_balance/2)-1
            
        POSITION_VALUE = margin_per_position * leverage

        return POSITION_VALUE
    

    except Exception as e:
        logger.error(f"Position Value fonksiyonunda hata: {e}")
        time.sleep(2)