import time
import sys
from utils.globals import set_sl_price

async def get_entry_price(symbol, client, logger):
    try:
        # Fetch position information asynchronously
        positions = await client.futures_position_information(symbol=symbol)
        
        # Check positions
        for pos in positions:
            if pos['symbol'] == symbol:
                position_amount = float(pos['positionAmt'])
                entry_price = float(pos['entryPrice'])
                
                if position_amount != 0:  # If position is open
                    return entry_price
                else:
                    return None

    except Exception as e:
        logger.error(f"{symbol} - Error in Get Entry Price function: {e}")
        return None

async def get_wallet_balance(client, logger):
    try:
        # Fetch account info asynchronously
        return float(await client.futures_account()['totalWalletBalance'])  # Return 0 if USDT not found
    except Exception as e:
        logger.error(f"Error in Get Wallet Balance Function: {e}")
        return 0

async def get_open_positions_count(client, logger):
    try:
        # Fetch position information asynchronously
        positions = await client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        return len(open_positions)
    except Exception as e:
        logger.error(f"Error in Open Position Count Function: {e}")
        return 0
    

async def check_balance_availability(capital_tbu, client, logger): 
    try:
        if capital_tbu < get_wallet_balance(client, logger):
            print("Insufficient balance or max positions. Please adjust.")
            time.sleep(10)
            sys.exit("Please adjust your balance or max positions.")
        
    except Exception as e:
        logger.error(f"Error while Cheching Balance Availability: {e}")
        return 0
    
async def set_stoploss_price(buyAll, symbol, close_prices_str, price_precision, logger):
    try:
        close_prices = (close_prices_str.astype(float))
        min_price = min(close_prices)
        max_price = max(close_prices)
        if buyAll:
            sl_price = round(min_price * 0.998, price_precision)
        else:
            sl_price = round(max_price * 1.002, price_precision)
        
        set_sl_price(sl_price, symbol)

    except Exception as e:
        logger.error(f"Error while Setting Stoploss Price: {e}")
        return 0