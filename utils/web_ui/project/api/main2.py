from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

app = FastAPI()

# Enable CORS - Allow requests from the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Temporary mock data until actual trading functions are integrated
MOCK_POSITIONS = [
    {
        "symbol": "BTCUSDT",
        "positionAmt": "0.5",
        "notional": "20000",
        "unRealizedProfit": "150.25",
        "entryPrice": "40000",
        "markPrice": "40300",
    }
]

MOCK_CONDITIONS = [
    {
        "symbol": "BTCUSDT",
        "fundingPeriod": True,
        "buyConditions": {
            "condA": True,
            "condB": False,
            "condC": True,
        },
        "sellConditions": {
            "condA": False,
            "condB": True,
            "condC": False,
        }
    }
]

@app.get("/api/positions")
async def get_positions():
    # Replace with actual data when ready
    return MOCK_POSITIONS

@app.get("/api/trading-conditions")
async def get_trading_conditions():
    # Replace with actual data when ready
    return MOCK_CONDITIONS

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)