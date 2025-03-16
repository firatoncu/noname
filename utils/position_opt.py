from utils.cursor_movement import clean_line

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
        logger.error(f"{symbol} için giriş fiyatı alınırken hata: {e}")
        return None

async def get_usdt_balance(client, logger):
    try:
        # Fetch account info asynchronously
        account_info = await client.futures_account()
        for asset in account_info['assets']:
            if asset['asset'] == 'USDT':
                return float(asset['availableBalance'])
        return 0  # Return 0 if USDT not found
    except Exception as e:
        logger.error(f"Bakiye alınırken hata: {e}")
        return 0

async def get_open_positions_count(client, logger):
    try:
        # Fetch position information asynchronously
        positions = await client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        return len(open_positions)
    except Exception as e:
        logger.error(f"Açık pozisyon sayısı alınırken hata: {e}")
        return 0