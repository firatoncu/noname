# ui.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
from utils.web_ui.update_web_ui import get_trading_conditions_ui, get_current_position_ui
import asyncio

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

# Initialize global variables with default empty lists
current_positions: List[Position] = []
trading_conditions: List[TradingConditions] = []

# FastAPI app setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/positions", response_model=List[Position])
async def get_positions():
    return current_positions

@app.get("/api/trading-conditions", response_model=List[TradingConditions])
async def get_trading_conditions():
    return trading_conditions

# Update UI values
async def update_ui_values(new_positions, new_conditions):
    global current_positions, trading_conditions
    current_positions = new_positions
    trading_conditions = new_conditions

# Updater loop
async def update_ui(symbols, client):
    while True:
        try:
            trading_conditions_data = await get_trading_conditions_ui(symbols)
            current_position_data = await get_current_position_ui(client)
            await update_ui_values(current_position_data, trading_conditions_data)
            await asyncio.sleep(1)  # Wait before retrying
        except Exception as e:
            print(f"Error in update_ui: {e}")  # Replace with proper logging if needed
        await asyncio.sleep(1)  # Wait before retrying

# Uvicorn server setup
def run_uvicorn():
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="error",
        loop="asyncio"
    )
    return uvicorn.Server(config)

async def start_server_and_updater(symbols, client):
    """Start both the server and updater as background tasks"""
    server = run_uvicorn()
    server_task = asyncio.create_task(server.serve())
    updater_task = asyncio.create_task(update_ui(symbols, client))
    return server_task, updater_task