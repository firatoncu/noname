from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Literal, Optional, Set, Any
import uvicorn
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import the utils modules
from utils.web_ui.update_web_ui import get_trading_conditions_ui, get_current_position_ui, get_last_5_positions, get_wallet_info
import asyncio
import json
import yaml
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC

# Define order types for Futures
ORDER_TYPE_TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'
ORDER_TYPE_STOP_MARKET = 'STOP_MARKET'

# Configuration models
class MarginConfig(BaseModel):
    mode: str
    fixed_amount: float
    percentage: float
    ask_user_selection: bool
    default_to_full_margin: bool
    user_response_timeout: int

class StrategyConfig(BaseModel):
    name: str
    type: str
    enabled: bool
    timeframe: str
    lookback_period: int

class RiskConfig(BaseModel):
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    risk_per_trade: float
    max_open_positions: int
    stop_loss_percentage: float
    take_profit_ratio: float

class TradingConfig(BaseModel):
    capital: float
    leverage: int
    margin: MarginConfig
    symbols: List[str]
    paper_trading: bool
    auto_start: bool
    strategy: StrategyConfig
    risk: RiskConfig

class ExchangeConfig(BaseModel):
    type: str
    testnet: bool
    rate_limit: int
    timeout: int
    retry_attempts: int

class LoggingConfig(BaseModel):
    level: str
    console_output: bool
    structured_logging: bool

class NotificationsConfig(BaseModel):
    enabled: bool

class ConfigData(BaseModel):
    trading: TradingConfig
    exchange: ExchangeConfig
    logging: LoggingConfig
    notifications: NotificationsConfig

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

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

# Position Analysis Models
class PositionAnalysisData(BaseModel):
    id: str
    symbol: str
    side: Literal['LONG', 'SHORT']
    entryPrice: float
    exitPrice: float
    quantity: float
    pnl: float
    pnlPercentage: float
    entryTime: str
    exitTime: str
    duration: int  # in minutes
    strategy: str
    leverage: int

class PerformanceMetrics(BaseModel):
    totalTrades: int
    winningTrades: int
    losingTrades: int
    winRate: float
    totalPnL: float
    averagePnL: float
    bestTrade: float
    worstTrade: float
    averageDuration: float
    sharpeRatio: float
    maxDrawdown: float
    profitFactor: float

class SymbolPerformance(BaseModel):
    symbol: str
    trades: int
    winRate: float
    totalPnL: float
    averagePnL: float

class AnalysisResponse(BaseModel):
    positions: List[PositionAnalysisData]
    metrics: PerformanceMetrics
    symbolPerformance: List[SymbolPerformance]

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
app = FastAPI(
    title="n0name Trading Bot API",
    description="API for n0name trading bot - provides real-time trading data and controls",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5173",
        "https://127.0.0.1:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "n0name Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "positions": "/api/positions",
            "trading_conditions": "/api/trading-conditions", 
            "wallet": "/api/wallet",
            "historical_positions": "/api/historical-positions",
            "config": "/api/config",
            "websocket": "/ws",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "frontend_url": "http://localhost:5173",
        "message": "API is running successfully! Visit the frontend at http://localhost:5173"
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "n0name Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "available_endpoints": [
            "GET /api/positions - Get current trading positions",
            "GET /api/trading-conditions - Get trading conditions for all symbols",
            "GET /api/wallet - Get wallet information",
            "GET /api/historical-positions - Get historical positions",
            "GET /api/config - Get bot configuration",
            "POST /api/config - Update bot configuration",
            "POST /api/close-position/{symbol} - Close a position",
            "POST /api/set-tpsl/{symbol} - Set take profit/stop loss",
            "POST /api/close-limit-orders/{symbol} - Close limit orders",
            "WebSocket /ws - Real-time data updates"
        ]
    }

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

@app.post("/api/refresh-trading-conditions")
async def refresh_trading_conditions():
    """Manually refresh trading conditions after config changes"""
    try:
        from utils.load_config import load_config
        current_config = load_config()
        current_symbols = current_config.get('trading', {}).get('symbols', [])
        if not current_symbols:
            # Fallback to legacy symbols format if trading.symbols is empty
            current_symbols = current_config.get('symbols', {}).get('symbols', [])
        
        if not current_symbols:
            return {"error": "No symbols found in configuration"}
        
        # Force update trading conditions with new symbols
        global trading_conditions
        from utils.web_ui.update_web_ui import get_trading_conditions_ui
        trading_conditions = await get_trading_conditions_ui(current_symbols)
        
        # Broadcast the update via WebSocket
        await manager.broadcast({
            "type": "trading_conditions_update",
            "data": [cond.dict() if hasattr(cond, 'dict') else cond for cond in trading_conditions]
        })
        
        return {"message": f"Trading conditions refreshed for {len(current_symbols)} symbols", "symbols": current_symbols}
    except Exception as e:
        print(f"Error refreshing trading conditions: {e}")
        return {"error": str(e)}

# Configuration management endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    try:
        print(f"API: Loading config using simplified load_config function")  # Debug logging
        
        # Use the simplified load_config function
        from utils.load_config import load_config
        bot_config = load_config()
        
        print(f"API: Successfully loaded config")  # Debug logging
        print(f"API: Config keys: {list(bot_config.keys())}")  # Debug logging
        
        # Validate required sections exist
        required_sections = ['trading', 'exchange', 'logging', 'notifications']
        missing_sections = [section for section in required_sections if section not in bot_config]
        if missing_sections:
            raise HTTPException(status_code=500, detail=f"Missing required config sections: {', '.join(missing_sections)}")
        
        # Extract values from the actual config - no defaults
        trading_config = bot_config['trading']
        exchange_config = bot_config['exchange']
        logging_config = bot_config['logging']
        notifications_config = bot_config['notifications']
        
        # Validate required trading fields
        required_trading_fields = ['capital', 'leverage', 'symbols', 'paper_trading', 'auto_start', 'strategy', 'risk']
        missing_trading = [field for field in required_trading_fields if field not in trading_config]
        if missing_trading:
            raise HTTPException(status_code=500, detail=f"Missing required trading config fields: {', '.join(missing_trading)}")
        
        # Validate required exchange fields
        required_exchange_fields = ['type', 'testnet', 'rate_limit', 'timeout', 'retry_attempts']
        missing_exchange = [field for field in required_exchange_fields if field not in exchange_config]
        if missing_exchange:
            raise HTTPException(status_code=500, detail=f"Missing required exchange config fields: {', '.join(missing_exchange)}")
        
        # Validate required logging fields
        required_logging_fields = ['level', 'console_output', 'structured_logging']
        missing_logging = [field for field in required_logging_fields if field not in logging_config]
        if missing_logging:
            raise HTTPException(status_code=500, detail=f"Missing required logging config fields: {', '.join(missing_logging)}")
        
        print(f"API: Final symbols to return: {trading_config['symbols']}")  # Debug logging
        print(f"API: Final logging level to return: {logging_config['level']}")  # Debug logging
        
        # Return the exact config structure without any defaults
        config_data = {
            "trading": {
                "capital": trading_config['capital'],
                "leverage": trading_config['leverage'],
                "margin": trading_config.get('margin', {}),
                "symbols": trading_config['symbols'],
                "paper_trading": trading_config['paper_trading'],
                "auto_start": trading_config['auto_start'],
                "strategy": trading_config['strategy'],
                "risk": trading_config['risk'],
            },
            "exchange": {
                "type": exchange_config['type'],
                "testnet": exchange_config['testnet'],
                "rate_limit": exchange_config['rate_limit'],
                "timeout": exchange_config['timeout'],
                "retry_attempts": exchange_config['retry_attempts'],
            },
            "logging": {
                "level": logging_config['level'],
                "console_output": logging_config['console_output'],
                "structured_logging": logging_config['structured_logging'],
            },
            "notifications": {
                "enabled": notifications_config.get('enabled', True),
            },
        }
        
        return config_data
    except Exception as e:
        print(f"API: Error loading config: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load configuration: {str(e)}")

@app.post("/api/config")
async def update_config(config: dict):
    """Update configuration"""
    try:
        # Use the simplified load_config function to get the config path
        from utils.load_config import load_config
        from pathlib import Path
        
        # Get the project root (parent of utils directory)
        project_root = Path(__file__).parent.parent.parent.parent.parent
        config_path = project_root / "config.yml"
        
        print(f"Updating config file at: {config_path}")  # Debug logging
        print(f"Received config data: {config}")  # Debug logging
        
        # Load the existing config to preserve other sections
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                existing_config = yaml.safe_load(file)
        else:
            raise HTTPException(status_code=404, detail="Configuration file not found")
        
        # Update the config sections based on the frontend data
        if "trading" in config:
            trading_config = config["trading"]
            
            # Update the new format trading section
            existing_config["trading"] = trading_config
            
            # Also update the legacy format fields for compatibility
            if "capital" in trading_config:
                existing_config["capital_tbu"] = trading_config["capital"]
            
            if "symbols" in trading_config:
                # Update the legacy symbols section
                if "symbols" not in existing_config:
                    existing_config["symbols"] = {}
                
                # IMPORTANT: Update both the legacy and new format symbols
                existing_config["symbols"]["symbols"] = trading_config["symbols"]
                existing_config["trading"]["symbols"] = trading_config["symbols"]
                
                if "leverage" in trading_config:
                    existing_config["symbols"]["leverage"] = trading_config["leverage"]
                
                if "risk" in trading_config and "max_open_positions" in trading_config["risk"]:
                    existing_config["symbols"]["max_open_positions"] = trading_config["risk"]["max_open_positions"]
        
        # Update other sections
        for section in ["exchange", "logging", "notifications"]:
            if section in config:
                existing_config[section] = config[section]
        
        print(f"Updated config structure:")  # Debug logging
        print(f"  capital_tbu: {existing_config.get('capital_tbu')}")
        print(f"  symbols.symbols: {existing_config.get('symbols', {}).get('symbols')}")
        print(f"  symbols.leverage: {existing_config.get('symbols', {}).get('leverage')}")
        print(f"  trading.symbols: {existing_config.get('trading', {}).get('symbols')}")
        
        # Write the updated config back to file
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(existing_config, file, default_flow_style=False, sort_keys=False)
        
        print("Config updated successfully")  # Debug logging
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        print(f"Error updating config: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

# Position Analysis endpoints
@app.get("/api/analysis/positions", response_model=List[PositionAnalysisData])
async def get_analysis_positions(
    timeframe: Optional[str] = "7d",
    symbol: Optional[str] = "all"
):
    """Get position data for analysis with optional filtering"""
    try:
        # For position analysis, we need more historical data than the regular endpoint
        # So we'll fetch directly from Binance if we have a client
        if binance_client is not None:
            print(f"DEBUG: Fetching extended historical data for analysis")
            historical_data = await get_extended_historical_positions(binance_client, timeframe)
        else:
            # Fallback to existing endpoint
            historical_data = await get_historical_positions()
        
        print(f"DEBUG: Retrieved {len(historical_data)} historical positions for analysis")
        
        if not historical_data:
            print("DEBUG: No historical positions available, using mock data")
            return await get_mock_analysis_positions(timeframe, symbol)
        
        # Convert historical positions to analysis format
        analysis_positions = []
        for pos in historical_data:
            try:
                # Handle both dict and object formats
                pos_dict = pos.dict() if hasattr(pos, 'dict') else pos
                
                # Calculate duration in minutes
                opened_at_str = pos_dict['openedAt']
                closed_at_str = pos_dict['closedAt']
                
                # Remove timezone info if present and parse
                if 'Z' in opened_at_str:
                    opened_at_str = opened_at_str.replace('Z', '')
                if 'Z' in closed_at_str:
                    closed_at_str = closed_at_str.replace('Z', '')
                
                # Parse datetime strings
                try:
                    opened_at = datetime.fromisoformat(opened_at_str)
                except:
                    # Try parsing as datetime string
                    opened_at = datetime.strptime(opened_at_str, '%Y-%m-%d %H:%M:%S')
                
                try:
                    closed_at = datetime.fromisoformat(closed_at_str)
                except:
                    # Try parsing as datetime string
                    closed_at = datetime.strptime(closed_at_str, '%Y-%m-%d %H:%M:%S')
                
                duration_minutes = (closed_at - opened_at).total_seconds() / 60
                
                # Get position data
                symbol_name = pos_dict['symbol']
                side = pos_dict['side']
                entry_price = float(pos_dict['entryPrice'])
                exit_price = float(pos_dict['exitPrice'])
                pnl = float(pos_dict['profit'])
                amount = float(pos_dict['amount'])
                
                # Calculate quantity and P&L percentage
                quantity = amount / entry_price if entry_price > 0 else 0
                
                if entry_price > 0:
                    pnl_percentage = ((exit_price - entry_price) / entry_price) * 100
                    if side == 'SHORT':
                        pnl_percentage = -pnl_percentage
                else:
                    pnl_percentage = 0
                
                analysis_positions.append(PositionAnalysisData(
                    id=f"{symbol_name}_{closed_at_str.replace(' ', '_').replace(':', '-')}",
                    symbol=symbol_name,
                    side=side,
                    entryPrice=entry_price,
                    exitPrice=exit_price,
                    quantity=quantity,
                    pnl=pnl,
                    pnlPercentage=pnl_percentage,
                    entryTime=opened_at_str,
                    exitTime=closed_at_str,
                    duration=int(duration_minutes),
                    strategy="Bollinger Bands & RSI",  # Default strategy name
                    leverage=5  # Default leverage
                ))
            except Exception as e:
                print(f"Error processing position {pos}: {e}")
                continue
        
        # Filter by timeframe (this is now done after getting more data)
        if timeframe != "all":
            now = datetime.now()
            if timeframe == "1d":
                cutoff = now - timedelta(days=1)
            elif timeframe == "7d":
                cutoff = now - timedelta(days=7)
            elif timeframe == "30d":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(days=7)  # Default to 7 days
            
            filtered_positions = []
            for p in analysis_positions:
                try:
                    # Parse the exitTime properly
                    exit_time_str = p.exitTime.replace('Z', '')
                    try:
                        exit_time = datetime.fromisoformat(exit_time_str)
                    except:
                        # Try parsing as datetime string format
                        exit_time = datetime.strptime(exit_time_str, '%Y-%m-%d %H:%M:%S')
                    
                    if exit_time >= cutoff:
                        filtered_positions.append(p)
                except Exception as e:
                    print(f"DEBUG: Error parsing exit time for position {p.symbol}: {e}")
                    # Include position if we can't parse the date
                    filtered_positions.append(p)
            
            analysis_positions = filtered_positions
        
        # Filter by symbol
        if symbol != "all":
            analysis_positions = [p for p in analysis_positions if p.symbol == symbol]
        
        # Sort by exit time (newest first)
        analysis_positions.sort(key=lambda x: x.exitTime, reverse=True)
        
        print(f"DEBUG: Returning {len(analysis_positions)} analysis positions after filtering")
        return analysis_positions
    except Exception as e:
        print(f"Error getting real analysis positions: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to mock data on error
        print("DEBUG: Falling back to mock data due to error")
        return await get_mock_analysis_positions(timeframe, symbol)

async def get_extended_historical_positions(client, timeframe: str):
    """Get extended historical positions for analysis with more data"""
    try:
        # Determine how many trades to fetch based on timeframe
        if timeframe == "1d":
            trade_limit = 500
        elif timeframe == "7d":
            trade_limit = 1000
        elif timeframe == "30d":
            trade_limit = 2000
        else:  # "all"
            trade_limit = 3000
        
        print(f"DEBUG: Fetching {trade_limit} trades for timeframe {timeframe}")
        
        # Import the extraction logic
        from utils.web_ui.update_web_ui import extract_position, HistoricalPosition, unix_milliseconds_to_datetime
        
        # Retrieve a larger batch of trades
        trades = await client.futures_account_trades(limit=trade_limit)
        # Sort trades descending by time (most recent first)
        trades.sort(key=lambda t: t['time'], reverse=True)
        positions = []
        i = 0
        n = len(trades)
        
        # Extract more positions (up to 200 for analysis)
        max_positions = 200 if timeframe == "all" else 100
        
        while i < n and len(positions) < max_positions:
            try:
                pos, new_index = extract_position(trades, i)
                positions.append(pos)
                # Update index to continue after the position's records.
                i = new_index
            except ValueError as e:
                # If extraction fails, break out.
                break
        
        print(f"DEBUG: Extracted {len(positions)} positions from {len(trades)} trades")
        return positions
    except Exception as e:
        print(f"Error getting extended historical positions: {e}")
        # Fallback to regular method
        from utils.web_ui.update_web_ui import get_last_5_positions
        return await get_last_5_positions(client)

@app.get("/api/analysis/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    timeframe: Optional[str] = "7d",
    symbol: Optional[str] = "all"
):
    """Get performance metrics for the specified timeframe and symbol"""
    try:
        # Get positions data
        positions = await get_analysis_positions(timeframe, symbol)
        
        if not positions:
            return PerformanceMetrics(
                totalTrades=0,
                winningTrades=0,
                losingTrades=0,
                winRate=0.0,
                totalPnL=0.0,
                averagePnL=0.0,
                bestTrade=0.0,
                worstTrade=0.0,
                averageDuration=0.0,
                sharpeRatio=0.0,
                maxDrawdown=0.0,
                profitFactor=0.0
            )
        
        # Calculate metrics
        winning_trades = len([p for p in positions if p.pnl > 0])
        losing_trades = len([p for p in positions if p.pnl < 0])
        total_pnl = sum(p.pnl for p in positions)
        pnls = [p.pnl for p in positions]
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0
        average_duration = sum(p.duration for p in positions) / len(positions)
        
        # Calculate max drawdown
        peak = 0
        max_drawdown = 0
        running_pnl = 0
        
        for pos in sorted(positions, key=lambda x: x.exitTime):
            running_pnl += pos.pnl
            if running_pnl > peak:
                peak = running_pnl
            if peak > 0:
                drawdown = (peak - running_pnl) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # Calculate profit factor
        gross_profit = sum(p.pnl for p in positions if p.pnl > 0)
        gross_loss = abs(sum(p.pnl for p in positions if p.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (999 if gross_profit > 0 else 0)
        
        # Simple Sharpe ratio calculation
        returns = [p.pnlPercentage for p in positions]
        avg_return = sum(returns) / len(returns) if returns else 0
        return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 0
        sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        
        return PerformanceMetrics(
            totalTrades=len(positions),
            winningTrades=winning_trades,
            losingTrades=losing_trades,
            winRate=(winning_trades / len(positions)) * 100,
            totalPnL=total_pnl,
            averagePnL=total_pnl / len(positions),
            bestTrade=best_trade,
            worstTrade=worst_trade,
            averageDuration=average_duration,
            sharpeRatio=sharpe_ratio,
            maxDrawdown=max_drawdown,
            profitFactor=profit_factor
        )
    except Exception as e:
        print(f"Error calculating performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/symbol-performance", response_model=List[SymbolPerformance])
async def get_symbol_performance(
    timeframe: Optional[str] = "7d"
):
    """Get performance metrics grouped by symbol"""
    try:
        # Get all positions for the timeframe
        positions = await get_analysis_positions(timeframe, "all")
        
        # Group by symbol
        symbol_groups = {}
        for pos in positions:
            if pos.symbol not in symbol_groups:
                symbol_groups[pos.symbol] = []
            symbol_groups[pos.symbol].append(pos)
        
        # Calculate metrics for each symbol
        symbol_performance = []
        for symbol, symbol_positions in symbol_groups.items():
            winning_trades = len([p for p in symbol_positions if p.pnl > 0])
            total_pnl = sum(p.pnl for p in symbol_positions)
            
            symbol_performance.append(SymbolPerformance(
                symbol=symbol,
                trades=len(symbol_positions),
                winRate=(winning_trades / len(symbol_positions)) * 100,
                totalPnL=total_pnl,
                averagePnL=total_pnl / len(symbol_positions)
            ))
        
        # Sort by total PnL descending
        symbol_performance.sort(key=lambda x: x.totalPnL, reverse=True)
        
        return symbol_performance
    except Exception as e:
        print(f"Error getting symbol performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/complete", response_model=AnalysisResponse)
async def get_complete_analysis(
    timeframe: Optional[str] = "7d",
    symbol: Optional[str] = "all"
):
    """Get complete analysis data including positions, metrics, and symbol performance"""
    try:
        positions = await get_analysis_positions(timeframe, symbol)
        metrics = await get_performance_metrics(timeframe, symbol)
        symbol_performance = await get_symbol_performance(timeframe)
        
        return AnalysisResponse(
            positions=positions,
            metrics=metrics,
            symbolPerformance=symbol_performance
        )
    except Exception as e:
        print(f"Error getting complete analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial data
        await websocket.send_text(json.dumps({
            "type": "positions_update",
            "data": [pos.dict() if hasattr(pos, 'dict') else pos for pos in current_positions]
        }))
        await websocket.send_text(json.dumps({
            "type": "trading_conditions_update", 
            "data": [cond.dict() if hasattr(cond, 'dict') else cond for cond in trading_conditions]
        }))
        await websocket.send_text(json.dumps({
            "type": "wallet_update",
            "data": wallet_info
        }))
        
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "refresh_data":
                    # Send current data
                    await websocket.send_text(json.dumps({
                        "type": "positions_update",
                        "data": [pos.dict() if hasattr(pos, 'dict') else pos for pos in current_positions]
                    }))
                    await websocket.send_text(json.dumps({
                        "type": "trading_conditions_update",
                        "data": [cond.dict() if hasattr(cond, 'dict') else cond for cond in trading_conditions]
                    }))
                    await websocket.send_text(json.dumps({
                        "type": "wallet_update",
                        "data": wallet_info
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": str(e)}
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Update UI values with WebSocket broadcasting
async def update_ui_values(new_positions, new_conditions, new_wallet, new_historical):
    global current_positions, trading_conditions, wallet_info, historical_positions
    
    # Check if data has changed before broadcasting
    positions_changed = current_positions != new_positions
    conditions_changed = trading_conditions != new_conditions
    wallet_changed = wallet_info != new_wallet
    
    # Update global variables
    wallet_info = new_wallet
    historical_positions = new_historical
    current_positions = new_positions
    trading_conditions = new_conditions
    
    # Broadcast updates via WebSocket
    if positions_changed:
        await manager.broadcast({
            "type": "positions_update",
            "data": [pos.dict() if hasattr(pos, 'dict') else pos for pos in current_positions]
        })
    
    if conditions_changed:
        await manager.broadcast({
            "type": "trading_conditions_update",
            "data": [cond.dict() if hasattr(cond, 'dict') else cond for cond in trading_conditions]
        })
    
    if wallet_changed:
        await manager.broadcast({
            "type": "wallet_update",
            "data": wallet_info
        })

# Updater loop
async def update_ui(symbols, client):
    while True:
        try:
            # Read symbols dynamically from config to pick up changes
            try:
                from utils.load_config import load_config
                current_config = load_config()
                current_symbols = current_config.get('trading', {}).get('symbols', symbols)
                if not current_symbols:
                    # Fallback to legacy symbols format if trading.symbols is empty
                    current_symbols = current_config.get('symbols', {}).get('symbols', symbols)
            except Exception as e:
                print(f"Warning: Could not load symbols from config, using original: {e}")
                current_symbols = symbols
            
            trading_conditions_data = await get_trading_conditions_ui(current_symbols)
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

# Uvicorn server setup with HTTPS support
def run_uvicorn():
    # Path to SSL certificates
    cert_dir = os.path.join(os.path.dirname(__file__), '..', 'certs')
    cert_file = os.path.join(cert_dir, 'localhost-cert.pem')
    key_file = os.path.join(cert_dir, 'localhost-key.pem')
    
    # Check if SSL certificates exist
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)
    
    if use_ssl:
        config = uvicorn.Config(
            app,
            host="localhost",
            port=8000,
            log_level="error",
            loop="asyncio",
            ssl_keyfile=key_file,
            ssl_certfile=cert_file
        )
        print("🔐 Starting HTTPS server on https://localhost:8000")
    else:
        config = uvicorn.Config(
            app,
            host="localhost",
            port=8000,
            log_level="error",
            loop="asyncio"
        )
        print("⚠️  SSL certificates not found. Starting HTTP server on http://localhost:8000")
        print("💡 Run: python utils/web_ui/generate_certificates.py to enable HTTPS")
    
    return uvicorn.Server(config)

async def start_server_and_updater(symbols, client):
    """Start both the server and updater as background tasks"""
    global binance_client
    binance_client = client
    server = run_uvicorn()
    server_task = asyncio.create_task(server.serve())
    updater_task = asyncio.create_task(update_ui(symbols, client))
    return server_task, updater_task

async def get_mock_analysis_positions(timeframe: str, symbol: str):
    """Fallback mock data generation"""
    import random
    from datetime import datetime, timedelta
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT']
    strategies = ['Bollinger Bands & RSI', 'MACD Crossover', 'Support/Resistance', 'EMA Crossover']
    positions = []
    
    # Generate 50 mock positions
    for i in range(50):
        pos_symbol = random.choice(symbols)
        side = random.choice(['LONG', 'SHORT'])
        entry_price = 100 + random.random() * 900
        pnl_percentage = (random.random() - 0.4) * 20  # Slightly positive bias
        exit_price = entry_price * (1 + pnl_percentage / 100)
        quantity = random.random() * 10 + 1
        pnl = (exit_price - entry_price) * quantity * (1 if side == 'LONG' else -1)
        
        # Generate realistic timestamps
        entry_time = datetime.now() - timedelta(days=random.random() * 30)
        duration_minutes = random.randint(30, 1440)  # 30 minutes to 24 hours
        exit_time = entry_time + timedelta(minutes=duration_minutes)
        
        positions.append(PositionAnalysisData(
            id=f"pos_{i}",
            symbol=pos_symbol,
            side=side,
            entryPrice=entry_price,
            exitPrice=exit_price,
            quantity=quantity,
            pnl=pnl,
            pnlPercentage=pnl_percentage,
            entryTime=entry_time.isoformat(),
            exitTime=exit_time.isoformat(),
            duration=duration_minutes,
            strategy=random.choice(strategies),
            leverage=5
        ))
    
    # Filter by timeframe
    if timeframe != "all":
        now = datetime.now()
        if timeframe == "1d":
            cutoff = now - timedelta(days=1)
        elif timeframe == "7d":
            cutoff = now - timedelta(days=7)
        elif timeframe == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=7)  # Default to 7 days
        
        positions = [p for p in positions if datetime.fromisoformat(p.exitTime) >= cutoff]
    
    # Filter by symbol
    if symbol != "all":
        positions = [p for p in positions if p.symbol == symbol]
    
    # Sort by exit time (newest first)
    positions.sort(key=lambda x: x.exitTime, reverse=True)
    
    return positions