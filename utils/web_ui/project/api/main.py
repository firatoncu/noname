from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Literal, Optional
import uvicorn
from utils.web_ui.update_web_ui import get_trading_conditions_ui, get_current_position_ui, get_last_5_positions, get_wallet_info
import asyncio
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC

# Define order types for Futures
ORDER_TYPE_TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'
ORDER_TYPE_STOP_MARKET = 'STOP_MARKET'

# Define data models for the API responses
class Position(BaseModel):
    symbol: str
    positionAmt: str
    notional: str
    unRealizedProfit: str
    entryPrice: str
    markPrice: str
    entryTime: str
    takeProfitPrice: Optional[str] = None
    stopLossPrice: Optional[str] = None

class TradingConditions(BaseModel):
    symbol: str
    fundingPeriod: bool
    trendingCondition: bool
    buyConditions: Dict[str, bool]
    sellConditions: Dict[str, bool]
    strategyName: str

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
    openedAt: str
    closedAt: str

class TPSLRequest(BaseModel):
    take_profit_percentage: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None

# Initialize global variables with default empty lists
current_positions: List[Position] = []
trading_conditions: List[TradingConditions] = []
wallet_info = {
    "totalBalance": "25000.00",
    "availableBalance": "15000.00",
    "unrealizedPnL": "150.25",
    "dailyPnL": "450.75",
    "weeklyPnL": "1250.50",
    "marginRatio": "15.5"
}
historical_positions = []
binance_client = None  # Initialize client as None

# FastAPI app setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80", "http://n0name"],  # Adjust for your frontend
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

@app.get("/api/wallet", response_model=WalletInfo)
async def get_wallet():
    return wallet_info

@app.get("/api/historical-positions", response_model=List[HistoricalPosition])
async def get_historical_positions():
    return historical_positions

@app.post("/api/close-position/{symbol}")
async def close_position(symbol: str):
    try:
        if binance_client is None:
            return {"error": "Trading client not initialized"}

        # Get the position to close
        position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if not position:
            return {"error": "Position not found"}

        # Calculate the side and quantity for closing
        position_amount = float(position['positionAmt'])
        if position_amount == 0:
            return {"error": "Position already closed"}

        # Cancel all open orders for this symbol
        try:
            await binance_client.futures_cancel_all_open_orders(symbol=symbol)
        except Exception as e:
            print(f"Error canceling orders: {e}")
            # Continue with position closure even if order cancellation fails

        # Close the position using market order
        side = SIDE_SELL if position_amount > 0 else SIDE_BUY
        quantity = abs(position_amount)

        # Close the position on Binance
        await binance_client.futures_create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )

        # Remove from current positions list
        current_positions[:] = [p for p in current_positions if p['symbol'] != symbol]

        return {"message": f"Position closed successfully for {symbol}"}
    except Exception as e:
        print(f"Error in close_position: {e}")  # Add logging
        return {"error": str(e)}

@app.post("/api/set-tpsl/{symbol}")
async def set_tpsl(symbol: str, request: TPSLRequest):
    try:
        if binance_client is None:
            return {"error": "Trading client not initialized"}

        # Get the position
        position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if not position:
            return {"error": "Position not found"}

        position_amount = float(position['positionAmt'])
        if position_amount == 0:
            return {"error": "Position already closed"}

        # Cancel any existing TP/SL orders for this symbol
        try:
            await binance_client.futures_cancel_all_open_orders(symbol=symbol)
        except Exception as e:
            print(f"Error canceling existing orders: {e}")
            # Continue with setting new TP/SL even if cancellation fails

        entry_price = float(position['entryPrice'])
        mark_price = float(position['markPrice'])
        is_long = position_amount > 0

        # Calculate prices if percentages are provided
        if request.take_profit_percentage is not None:
            take_profit_price = entry_price * (1 + request.take_profit_percentage/100) if is_long else entry_price * (1 - request.take_profit_percentage/100)
        else:
            take_profit_price = request.take_profit_price

        if request.stop_loss_percentage is not None:
            stop_loss_price = entry_price * (1 - request.stop_loss_percentage/100) if is_long else entry_price * (1 + request.stop_loss_percentage/100)
        else:
            stop_loss_price = request.stop_loss_price

        # Validate TP/SL prices based on position type
        if is_long:
            # For long positions
            if take_profit_price is not None:
                if take_profit_price <= max(entry_price, mark_price):
                    return {"error": "Take profit price must be higher than both entry and current price for long positions"}
            if stop_loss_price is not None:
                if stop_loss_price >= min(entry_price, mark_price):
                    return {"error": "Stop loss price must be lower than both entry and current price for long positions"}
        else:
            # For short positions
            if take_profit_price is not None:
                if take_profit_price >= min(entry_price, mark_price):
                    return {"error": "Take profit price must be lower than both entry and current price for short positions"}
            if stop_loss_price is not None:
                if stop_loss_price <= max(entry_price, mark_price):
                    return {"error": "Stop loss price must be higher than both entry and current price for short positions"}

        # Set take profit
        if take_profit_price is not None:
            await binance_client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL if is_long else SIDE_BUY,
                type=ORDER_TYPE_TAKE_PROFIT_MARKET,
                stopPrice=take_profit_price,
                closePosition=True
            )

        # Set stop loss
        if stop_loss_price is not None:
            await binance_client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL if is_long else SIDE_BUY,
                type=ORDER_TYPE_STOP_MARKET,
                stopPrice=stop_loss_price,
                closePosition=True
            )

        return {"message": f"TP/SL set successfully for {symbol}"}
    except Exception as e:
        print(f"Error in set_tpsl: {e}")
        return {"error": str(e)}

@app.post("/api/close-limit-orders/{symbol}")
async def close_limit_orders(symbol: str, order_type: Optional[str] = None):
    try:
        if binance_client is None:
            return {"error": "Trading client not initialized"}

        # Get the position
        position = next((p for p in current_positions if p['symbol'] == symbol), None)
        if not position:
            return {"error": "Position not found"}

        # Get all open orders for this symbol
        open_orders = await binance_client.futures_get_open_orders(symbol=symbol)
        
        if order_type:
            # Cancel specific order type (TP or SL)
            for order in open_orders:
                if (order_type == 'TP' and order['type'] == 'TAKE_PROFIT_MARKET') or \
                   (order_type == 'SL' and order['type'] == 'STOP_MARKET'):
                    try:
                        await binance_client.futures_cancel_order(
                            symbol=symbol,
                            orderId=order['orderId']
                        )
                    except Exception as e:
                        print(f"Error canceling specific order: {e}")
                        continue
            return {"message": f"{order_type} order closed successfully for {symbol}"}
        else:
            # Cancel all open orders
            try:
                await binance_client.futures_cancel_all_open_orders(symbol=symbol)
                return {"message": f"All limit orders closed successfully for {symbol}"}
            except Exception as e:
                print(f"Error canceling all orders: {e}")
                return {"error": str(e)}
    except Exception as e:
        print(f"Error in close_limit_orders: {e}")
        return {"error": str(e)}

# Update UI values
async def update_ui_values(new_positions, new_conditions, new_wallet, new_historical):
    global current_positions, trading_conditions, wallet_info, historical_positions
    wallet_info = new_wallet
    historical_positions = new_historical
    current_positions = new_positions
    trading_conditions = new_conditions

# Updater loop
async def update_ui(symbols, client):
    while True:
        try:
            trading_conditions_data = await get_trading_conditions_ui(symbols)
            current_position_data = await get_current_position_ui(client)
            wallet_data = await get_wallet_info(client)
            historical_data = await get_last_5_positions(client)

            await update_ui_values(
                current_position_data, 
                trading_conditions_data,
                wallet_data,
                historical_data)
            
            await asyncio.sleep(1)  # Wait before retrying
        except Exception as e:
            print(f"Error in update_ui: {e}")  # Replace with proper logging if needed
        await asyncio.sleep(1)  # Wait before retrying

# Uvicorn server setup
def run_uvicorn():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="error",
        loop="asyncio"
    )
    return uvicorn.Server(config)

async def start_server_and_updater(symbols, client):
    """Start both the server and updater as background tasks"""
    global binance_client
    binance_client = client
    server = run_uvicorn()
    server_task = asyncio.create_task(server.serve())
    updater_task = asyncio.create_task(update_ui(symbols, client))
    return server_task, updater_task