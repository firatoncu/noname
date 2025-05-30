import sys
import os
import asyncio
import webbrowser
from pathlib import Path

# Add parent directory to path to find utils module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from utils.enhanced_logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Start npm run dev in the background or serve static files for executable

async def serve_static_frontend():
    """Serve static frontend files for PyInstaller executable"""
    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        # Find the web_ui directory relative to the executable
        if getattr(sys, 'frozen', False):
            # PyInstaller executable - look for web_ui in the same directory
            exe_dir = Path(sys.executable).parent
            static_dir = exe_dir / "web_ui"
        else:
            # Development mode fallback
            static_dir = Path(__file__).parent.parent.parent / "dist" / "n0name_trading_bot_distribution" / "web_ui"
        
        if not static_dir.exists():
            logger.warning(f"Static frontend files not found at: {static_dir}")
            logger.info("Frontend will not be available")
            return None
        
        logger.info(f"Serving static frontend from: {static_dir}")
        
        # Create FastAPI app for static files
        app = FastAPI(title="n0name Frontend")
        
        # Mount static files
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="static")
        
        # Serve index.html for all routes (SPA routing)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            else:
                return {"error": "Frontend files not found"}
        
        # Start the static server
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=5173,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        
        # Open browser
        webbrowser.open("http://localhost:5173")
        logger.info("Started static frontend server - Opening http://localhost:5173")
        
        # Run server in background
        await server.serve()
        return server
        
    except Exception as e:
        logger.error(f"Error starting static frontend server: {e}")
        return None

async def run_npm_dev():
    try:
        if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
            # For PyInstaller executables, serve static files instead of npm dev
            logger.info("Running as executable - Starting static frontend server")
            return await serve_static_frontend()
        else:  # Running as a Python script
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Verify the project directory exists
        full_path = os.path.join(base_path, "project")
        if not os.path.exists(full_path):
            logger.warning(f"Frontend project directory not found: {full_path}")
            logger.info("Frontend development server will not start")
            return None

        # Check for npm
        npm_path = os.path.join(base_path, "project", "nodejs", "npm.cmd")
        if not os.path.exists(npm_path):
            # Try system npm as fallback
            npm_path = "npm"
            logger.info("Using system npm (project npm not found)")

        process = await asyncio.create_subprocess_shell(
            f'"{npm_path}" run dev',
            cwd=full_path,
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