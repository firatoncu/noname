from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Literal
import uvicorn
import asyncio
from utils.web_ui.update_web_ui import get_trading_conditions_ui, get_current_position_ui

# Define data models for the API responses
class Position(BaseModel):
    symbol: str
    positionAmt: str
    notional: str
    unRealizedProfit: str
    entryPrice: str
    markPrice: str

class TradingConditions(BaseModel):
    symbol: str
    fundingPeriod: bool
    buyConditions: Dict[str, bool]
    sellConditions: Dict[str, bool]

class WalletInfo(BaseModel):
    totalBalance: str
    availableBalance: str
    unrealizedPnL: str
    dailyPnL: str
    weeklyPnL: str
    marginRatio: str

class HistoricalPosition(BaseModel):
    symbol: str
    entryPrice: str
    exitPrice: str
    profit: str
    amount: str
    side: Literal['LONG', 'SHORT']
    closedAt: str

# Global state
current_positions = []
trading_conditions = []
wallet_info = {
    "totalBalance": "25000.00",
    "availableBalance": "15000.00",
    "unrealizedPnL": "150.25",
    "dailyPnL": "450.75",
    "weeklyPnL": "1250.50",
    "marginRatio": "15.5"
}
historical_positions = []

# Create FastAPI app instance
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/positions", response_model=List[Position])
async def get_positions():
    global current_positions
    return current_positions

@app.get("/api/trading-conditions", response_model=List[TradingConditions])
async def get_trading_conditions():
    global trading_conditions
    return trading_conditions

@app.get("/api/wallet", response_model=WalletInfo)
async def get_wallet():
    global wallet_info
    return wallet_info

@app.get("/api/historical-positions", response_model=List[HistoricalPosition])
async def get_historical_positions():
    global historical_positions
    return historical_positions

async def update_ui_values(new_positions, new_conditions, new_wallet, new_historical):
    global current_positions, trading_conditions, wallet_info, historical_positions
    current_positions = new_positions
    trading_conditions = new_conditions
    wallet_info = new_wallet
    historical_positions = new_historical

async def update_ui(symbols, client):
    while True:
        try:
            trading_conditions_data = await get_trading_conditions_ui(symbols)
            current_position_data = await get_current_position_ui(client)
            
            # You would implement these functions in your utils
            wallet_data = await get_wallet_info(client)
            historical_data = await get_historical_positions(client)
            
            await update_ui_values(
                current_position_data, 
                trading_conditions_data,
                wallet_data,
                historical_data
            )
            await asyncio.sleep(1)  # Update every second
        except Exception as e:
            print(f"Error updating UI: {e}")
            await asyncio.sleep(1)  # Wait before retrying

async def start_server_and_updater(symbols, client):
    """
    Async function to start both the server and updater tasks.
    """
    # Create the server config
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Create tasks for both the server and updater
    server_task = asyncio.create_task(server.serve())
    updater_task = asyncio.create_task(update_ui(symbols, client))
    
    try:
        # Wait for both tasks to complete (they won't unless there's an error)
        await asyncio.gather(server_task, updater_task)
    except Exception as e:
        print(f"Error in server or updater: {e}")
    finally:
        # Ensure both tasks are cancelled on shutdown
        server_task.cancel()
        updater_task.cancel()

def run_server(symbols, client):
    """
    Main entry point to run the server and updater.
    This should be called from your main application.
    """
    asyncio.run(start_server_and_updater(symbols, client))

if __name__ == "__main__":
    # For testing purposes only
    run_server([], None)