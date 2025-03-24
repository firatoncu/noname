from utils.globals import set_funding_flag
from datetime import datetime

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
        wallet_balance = await client.futures_account() # Return 0 if USDT not found
        wallet_balance = float(wallet_balance['totalWalletBalance']) - 3
        return wallet_balance
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
    
    
async def funding_fee_controller(symbol, client, logger):
    try:
        # Fetch funding rate
        next_funding_time = await client.futures_mark_price(symbol=symbol)
        next_funding_time = next_funding_time['nextFundingTime']
        if (float(next_funding_time) - round(datetime.timestamp(datetime.now()) * 1000))/1000 > 1200:
            set_funding_flag(True, symbol)
            return True
        else:
            set_funding_flag(False, symbol)
            return False
    except Exception as e:
        logger.error(f"Error in Funding Fee Controller: {e}")
        return None