"""
There are many things that humans are better at than computers. For example: Creativity and Art, Emotional Intelligence and Empathy, Context Understanding and Flexibility, Moral and Ethical Decisions, Intuition and Experience-Based Learning... These examples can be multiplied, but for all that, computers are fundamentally better than humans in only two areas: Processing Speed and Processing Capacity. 

What if we tried to combine the ways in which these two species are superior to each other?

A set of ideas grounded in human creativity, understanding of context, flexibility, intuition-based learning, and the near limitless computational power of the computer. This whole is my vision. 

With the structure to be created within the framework of this whole, certain patterns can be identified on random structures. There are two fundamental problems here. Identifying the right patterns and realizing the patterns at the desired frequency. 

Is absolute randomness possible? Can randomnesses differ from each other? Can certain patterns be found even within randomness? 

why n0t?"""

# Main entry point for the async trading bot application.
import warnings
import asyncio
from datetime import datetime
from binance import AsyncClient  # Replace synchronous Client with AsyncClient
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments  # Must be made async
from utils.logging import error_logger_func
from utils.current_status import current_status  # Assumed to be async
from src.open_position import open_position  # Assumed to be async
from auth.key_enryption import decrypt_api_keys
from utils.globals import set_db_status, get_error_counter
from utils.influxdb.inf_db_initializer import inf_db_init_main

warnings.filterwarnings("ignore", category=FutureWarning)

async def main():
    # Initialize logger and config
    logger = error_logger_func()
    config = load_config()

    # Extract configuration details
    symbol_config = config['symbols']
    leverage = symbol_config['leverage']
    max_open_positions = symbol_config['max_open_positions']
    symbols = symbol_config['symbols']
    capital_tbu = config['capital_tbu']
    
    
    api_key, api_secret = decrypt_api_keys()

    db_status = input("Do you want to use the InfluxDB? (y/n): ").strip().lower()
    if db_status == "y":
        set_db_status(True)
        inf_db_init_main()
    else:
        set_db_status(False)


    
    # Ask user to choose between Backtesting and Trading
    """mode = input("\n\nChoose mode (Backtesting/Trading): ").strip().lower()
    while mode not in ["backtesting", "trading"]:
        print("Invalid mode. Please choose 'Backtesting' or 'Trading'.")
        mode = input("Choose mode (Backtesting/Trading): ").strip().lower()
    if mode == "backtesting":
        client = Client(api_key, api_secret)
        backtest_pipeline(client, logger)

    elif mode == "trading":"""
    try:
        # Create AsyncClient instance
        client = await AsyncClient.create(api_key, api_secret)
        # Perform initial adjustments asynchronously
        
        await initial_adjustments(leverage, symbols, capital_tbu, client, logger)

        # Run the main loop indefinitely
        while get_error_counter() < 3:
            if datetime.now().second % 2 == 0:
                await open_position(max_open_positions, symbols, logger, client, leverage)
                await current_status(symbols)
                await asyncio.sleep(1)  # Prevent tight looping; adjust as needed

        if get_error_counter >= 3:
            logger.error("Too many errors occurred. Exiting the bot...")

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Clean up the client connection
        await client.close_connection()

# Entry point to run the async application
if __name__ == "__main__":
    asyncio.run(main())