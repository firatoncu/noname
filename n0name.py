# Main entry point for the async trading bot application.
import warnings
import asyncio
import os
from binance import AsyncClient  # Replace synchronous Client with AsyncClient
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments  # Must be made async
from utils.logging import error_logger_func
from utils.current_status import current_status  # Assumed to be async
from src.open_position import open_position  # Assumed to be async
from src.backtesting.backtest_pipeline import backtest_pipeline 
from binance.client import Client
from auth.key_enryption import decrypt_api_keys

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
        while True:
            await open_position(max_open_positions, symbols, logger, client, leverage)
            await current_status(symbols)
            await asyncio.sleep(2)  # Prevent tight looping; adjust as needed

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Clean up the client connection
        await client.close_connection()

# Entry point to run the async application
if __name__ == "__main__":
    asyncio.run(main())