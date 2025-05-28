import asyncio
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from src.create_order import check_create_order
from src.position_value import position_val
from src.control_position import position_checker
from utils.calculate_quantity import calculate_quantity
from utils.stepsize_precision import stepsize_precision
from utils.globals import get_capital_tbu, get_db_status
from utils.position_opt import funding_fee_controller
from utils.fetch_data import binance_fetch_data
from utils.influxdb.csv_writer import write_to_daily_csv
from utils.influxdb.inf_send_data import write_live_conditions


# Async function to process a single symbol
async def process_symbol(symbol, client, logger, stepSizes, quantityPrecisions, position_value):
    try:
        
        funding_fee = await funding_fee_controller(symbol, client, logger)
        if funding_fee == False:
            return

        df, close_price = await binance_fetch_data(500, symbol, client)
        Q = calculate_quantity(position_value, close_price, stepSizes[symbol], quantityPrecisions[symbol])

        await check_create_order(symbol, Q, df, client, logger)
        if get_db_status() == True:
            await write_live_conditions(df['timestamp'].iloc[-1], symbol)

    except Exception as e:
        logger.error(f"{symbol} işlenirken hata: {e}")

# Main async function
async def open_position(max_open_positions, symbols, logger, client, leverage, config=None):
    """
    Open trading positions based on market analysis.
    
    Args:
        max_open_positions: Maximum number of concurrent positions
        symbols: List of trading symbols
        logger: Logger instance
        client: Binance client
        leverage: Trading leverage
        config: Configuration dictionary for margin selection
    """
    try:
        # Fetch static data once
        stepSizes, quantityPrecisions, pricePrecisions = await stepsize_precision(client, symbols)
        capital_tbu = get_capital_tbu()
        
        # Calculate position value with margin selection support
        position_value = await position_val(leverage, capital_tbu, max_open_positions, logger, client, config)
        
        await position_checker(client, pricePrecisions, logger)
        

        # Create a list of tasks for each symbol
        tasks = [
            process_symbol(
                symbol, client, logger, 
                stepSizes, quantityPrecisions, position_value
            )
            for symbol in symbols
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Ana döngüde hata: {e}")
        await asyncio.sleep(2)