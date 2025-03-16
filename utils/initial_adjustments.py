from utils.globals import set_clean_sell_signal, set_clean_buy_signal
import asyncio

async def initial_adjustments(leverage, symbols, client, logger):
    try:
        for symbol in symbols:
            set_clean_sell_signal(False, symbol)
            set_clean_buy_signal(False, symbol)
            await client.futures_change_leverage(symbol=symbol, leverage=leverage)
        print("""
    
        ______                                                _ _                _                
       / __   |                           _                  | (_)              | |          _    
 ____ | | //| |____   ____ ____   ____   | |_   ____ ____  _ | |_ ____   ____   | | _   ___ | |_  
|  _ \| |// | |  _ \ / _  |    \ / _  )  |  _) / ___) _  |/ || | |  _ \ / _  |  | || \ / _ \|  _) 
| | | |  /__| | | | ( ( | | | | ( (/ /   | |__| |  ( ( | ( (_| | | | | ( ( | |  | |_) ) |_| | |__ 
|_| |_|\_____/|_| |_|\_||_|_|_|_|\____)   \___)_|   \_||_|\____|_|_| |_|\_|| |  |____/ \___/ \___)
                                                                       (_____|                    

          """)
        logger.info("Starting the bot...")
        await asyncio.sleep(3)  # Prevent tight looping; adjust as needed
        logger.info("Initial adjustments completed, starting main loop...")
        await asyncio.sleep(1)  # Prevent tight looping; adjust as needed
        logger.info(f"Current Crypto Pairs: {symbols}")
    except Exception as e:
        logger.error(f"Initial adjustments failed: {e}")