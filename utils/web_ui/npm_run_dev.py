import sys
import os
import asyncio
import webbrowser

# Add parent directory to path to find utils module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from utils.enhanced_logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
# Start npm run dev in the background

async def run_npm_dev():
    try:
        if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:  # Running as a Python script
            base_path = os.path.dirname(os.path.abspath(__file__))

        full_path = os.path.join(base_path, rf"project")
        npm_path = os.path.join(base_path, rf"project\nodejs\npm.cmd")

        process = await asyncio.create_subprocess_shell(
            f'"{npm_path}" run dev',
            cwd=full_path ,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Open localhost URL instead of custom domain
        webbrowser.open("http://localhost:5173")
        logger.info("Started npm run dev - Opening http://localhost:5173")
        return process

    except Exception as e:
        logger.error(f"Error in start_frontend: {e}")
        return None
    
async def start_frontend():
    """Start both the server and updater as background tasks"""
    npm_runner = asyncio.create_task(run_npm_dev())

    return npm_runner