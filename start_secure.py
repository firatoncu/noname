#!/usr/bin/env python3
"""
Secure startup script for n0name Trading Bot
Uses the secure API with authentication and encryption.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auth.secure_config import get_secure_config_manager
from utils.web_ui.project.api.secure_main import start_secure_server_and_updater
from utils.enhanced_logging import get_logger
from binance import AsyncClient

async def main():
    logger = get_logger("secure_startup")
    
    try:
        # Load secure configuration
        secure_config = get_secure_config_manager()
        config_data = secure_config.load_secure_config()
        
        if not config_data:
            print("❌ Failed to load secure configuration!")
            print("Please run: python setup_security.py --setup-config")
            return
        
        # Get API credentials
        api_creds = secure_config.get_api_credentials()
        if not api_creds:
            print("❌ No API credentials found in secure configuration!")
            return
        
        # Initialize Binance client
        client = await AsyncClient.create(
            api_creds['api_key'],
            api_creds['api_secret']
        )
        
        # Define trading symbols (modify as needed)
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
        
        logger.info("Starting secure trading bot...")
        
        # Start secure server and updater
        server_task, updater_task = await start_secure_server_and_updater(symbols, client)
        
        # Wait for tasks to complete
        await asyncio.gather(server_task, updater_task)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    finally:
        if 'client' in locals():
            await client.close_connection()

if __name__ == "__main__":
    asyncio.run(main())
