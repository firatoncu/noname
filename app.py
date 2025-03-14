# Main entry point for the async trading bot application.
import asyncio
from binance import AsyncClient  # Replace synchronous Client with AsyncClient
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments  # Must be made async
from utils.logging import logger_func
from src.open_position import open_position  # Assumed to be async

async def main():
    # Initialize logger and config
    logger = logger_func()
    config = load_config()

    # Extract configuration details
    api_config = config['api_keys']
    symbol_config = config['symbols']
    leverage = symbol_config['leverage']
    max_open_positions = symbol_config['max_open_positions']
    symbols = symbol_config['symbols']
    
    # Create AsyncClient instance
    client = await AsyncClient.create(api_config['api_key'], api_config['secret'])
    
    logger.info("Initial adjustments completed, starting main loop...")
    try:
        # Perform initial adjustments asynchronously
        await initial_adjustments(leverage, symbols, client, logger)

        # Run the main loop indefinitely
        while True:
            await open_position(max_open_positions, symbols, logger, client, leverage)
            await asyncio.sleep(1)  # Prevent tight looping; adjust as needed

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Clean up the client connection
        await client.close_connection()

# Entry point to run the async application
if __name__ == "__main__":
    asyncio.run(main())