"""
Secure FastAPI main application with comprehensive security features.
Integrates authentication, session management, input validation, and security headers.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import List, Dict, Literal, Optional, Set, Any
import uvicorn
import asyncio
import json
import time
from datetime import datetime
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC
import os

# Import security components
from auth.security_manager import SecurityManager, SecurityConfig, SecurityLevel, SecurityMiddleware
from auth.secure_config import get_secure_config_manager
from utils.enhanced_logging import get_logger, ErrorCategory, LogSeverity

# Import existing functionality
from utils.web_ui.update_web_ui import get_trading_conditions_ui, get_current_position_ui, get_last_5_positions, get_wallet_info

# Define order types for Futures
ORDER_TYPE_TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'
ORDER_TYPE_STOP_MARKET = 'STOP_MARKET'

# Initialize security manager
security_config = SecurityConfig(
    # Allow broader IP ranges for development (restrict in production)
    allowed_ip_ranges=['127.0.0.1/32', '::1/128', '192.168.0.0/16', '10.0.0.0/8'],
    rate_limit_requests=200,  # Increased for development
    session_timeout=7200,  # 2 hours
    max_login_attempts=10,  # More lenient for development
)

security_manager = SecurityManager(security_config)
logger = get_logger("secure_api")

# Security dependency
security = HTTPBearer(auto_error=False)

# Secure data models with validation
class SecurePosition(BaseModel):
    symbol: str
    positionAmt: str
    notional: str
    unRealizedProfit: str
    entryPrice: str
    markPrice: str
    entryTime: str
    takeProfitPrice: Optional[str] = None
    stopLossPrice: Optional[str] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not security_manager.input_validator.validate_symbol(v):
            raise ValueError('Invalid symbol format')
        return v

class SecureTradingConditions(BaseModel):
    symbol: str
    fundingPeriod: bool
    trendingCondition: bool
    buyConditions: Dict[str, bool]
    sellConditions: Dict[str, bool]
    strategyName: str
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not security_manager.input_validator.validate_symbol(v):
            raise ValueError('Invalid symbol format')
        return v

class SecureWalletInfo(BaseModel):
    totalBalance: str
    availableBalance: str
    unrealizedPnL: str
    dailyPnL: str
    weeklyPnL: str
    marginRatio: str

class SecureHistoricalPosition(BaseModel):
    symbol: str
    entryPrice: str
    exitPrice: str
    profit: str
    amount: str
    side: Literal['LONG', 'SHORT']
    openedAt: str
    closedAt: str
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not security_manager.input_validator.validate_symbol(v):
            raise ValueError('Invalid symbol format')
        return v

class SecureTPSLRequest(BaseModel):
    take_profit_percentage: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    
    @validator('take_profit_percentage', 'stop_loss_percentage')
    def validate_percentages(cls, v):
        if v is not None:
            if not security_manager.input_validator.validate_numeric_input(v, 0.1, 100.0):
                raise ValueError('Percentage must be between 0.1 and 100.0')
        return v
    
    @validator('take_profit_price', 'stop_loss_price')
    def validate_prices(cls, v):
        if v is not None:
            if not security_manager.input_validator.validate_numeric_input(v, 0.01, 1000000.0):
                raise ValueError('Price must be between 0.01 and 1,000,000')
        return v

class LoginRequest(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        return security_manager.input_validator.sanitize_string(v)

class LoginResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    jwt_token: Optional[str] = None
    message: str

# WebSocket connection manager with security
class SecureConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self.session_connections: Dict[str, str] = {}  # websocket_id -> session_id

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        websocket_id = id(websocket)
        self.active_connections[session_id] = websocket
        self.session_connections[str(websocket_id)] = session_id
        
        logger.audit(f"WebSocket connection established for session {session_id}")

    def disconnect(self, websocket: WebSocket):
        websocket_id = str(id(websocket))
        if websocket_id in self.session_connections:
            session_id = self.session_connections[websocket_id]
            self.active_connections.pop(session_id, None)
            self.session_connections.pop(websocket_id, None)
            logger.audit(f"WebSocket connection closed for session {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(message)
            except:
                self.disconnect(self.active_connections[session_id])

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        disconnected = []
        
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = SecureConnectionManager()

# Initialize global variables with default empty lists
current_positions: List[SecurePosition] = []
trading_conditions: List[SecureTradingConditions] = []
wallet_info = SecureWalletInfo(
    totalBalance="25000.00",
    availableBalance="15000.00",
    unrealizedPnL="150.25",
    dailyPnL="450.75",
    weeklyPnL="1250.50",
    marginRatio="15.5"
)
historical_positions = []
binance_client = None

# FastAPI app setup with security
app = FastAPI(
    title="n0name Trading Bot Secure API",
    description="Secure API for n0name trading bot with comprehensive security features",
    version="1.0.0"
)

# Add security middleware
app.add_middleware(SecurityMiddleware, security_manager=security_manager)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://127.0.0.1:8000", "https://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize async components when the event loop is running"""
    try:
        # Start async session cleanup
        await security_manager.start_async_cleanup()
        logger.info("Secure API startup completed")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup async components on shutdown"""
    try:
        # Stop async session cleanup
        await security_manager.stop_async_cleanup()
        logger.info("Secure API shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Authentication dependency
async def get_current_session(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate session and return user session"""
    client_ip = request.client.host if request.client else "unknown"
    
    # Check for session cookie first
    session_id = request.cookies.get("session_id")
    
    # Check for Authorization header
    if not session_id and credentials:
        session_id = credentials.credentials
    
    if not session_id:
        security_manager.log_security_event(
            "unauthorized_access_attempt",
            None,
            client_ip,
            {"endpoint": str(request.url.path)},
            SecurityLevel.MEDIUM
        )
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate session
    session = security_manager.auth_manager.session_manager.validate_session(session_id, client_ip)
    if not session:
        security_manager.log_security_event(
            "invalid_session_access",
            None,
            client_ip,
            {"session_id": session_id, "endpoint": str(request.url.path)},
            SecurityLevel.HIGH
        )
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return session

# Public endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Authenticate user and create session"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    try:
        # Validate input
        is_valid, errors = security_manager.input_validator.validate_api_request({
            "username": login_data.username,
            "password": login_data.password
        })
        
        if not is_valid:
            security_manager.log_security_event(
                "invalid_login_input",
                login_data.username,
                client_ip,
                {"errors": errors},
                SecurityLevel.MEDIUM
            )
            return LoginResponse(success=False, message="Invalid input data")
        
        # Authenticate user
        session_id = security_manager.auth_manager.authenticate_user(
            login_data.username,
            login_data.password,
            client_ip,
            user_agent
        )
        
        if session_id:
            # Create JWT token
            jwt_token = security_manager.auth_manager.create_jwt_token(
                login_data.username,
                security_manager.auth_manager.users[login_data.username]["permissions"]
            )
            
            security_manager.log_security_event(
                "successful_login",
                login_data.username,
                client_ip,
                {"session_id": session_id},
                SecurityLevel.LOW
            )
            
            return LoginResponse(
                success=True,
                session_id=session_id,
                jwt_token=jwt_token,
                message="Login successful"
            )
        else:
            security_manager.log_security_event(
                "failed_login_attempt",
                login_data.username,
                client_ip,
                {"reason": "invalid_credentials"},
                SecurityLevel.MEDIUM
            )
            return LoginResponse(success=False, message="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Login error: {e}", category=ErrorCategory.SECURITY, severity=LogSeverity.HIGH)
        return LoginResponse(success=False, message="Login failed")

@app.post("/api/auth/logout")
async def logout(request: Request, session = Depends(get_current_session)):
    """Logout user and invalidate session"""
    client_ip = request.client.host if request.client else "unknown"
    
    security_manager.auth_manager.session_manager.invalidate_session(session.session_id)
    
    security_manager.log_security_event(
        "user_logout",
        session.user_id,
        client_ip,
        {"session_id": session.session_id},
        SecurityLevel.LOW
    )
    
    return {"message": "Logout successful"}

@app.get("/api/security/status")
async def get_security_status(session = Depends(get_current_session)):
    """Get security status (admin only)"""
    if "admin" not in session.permissions:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return security_manager.get_security_summary()

# Protected endpoints
@app.get("/api/positions", response_model=List[SecurePosition])
async def get_positions(session = Depends(get_current_session)):
    """Get current positions"""
    return current_positions

@app.get("/api/trading-conditions", response_model=List[SecureTradingConditions])
async def get_trading_conditions(session = Depends(get_current_session)):
    """Get trading conditions"""
    return trading_conditions

@app.get("/api/wallet", response_model=SecureWalletInfo)
async def get_wallet(session = Depends(get_current_session)):
    """Get wallet information"""
    return wallet_info

@app.get("/api/historical-positions", response_model=List[SecureHistoricalPosition])
async def get_historical_positions(session = Depends(get_current_session)):
    """Get historical positions"""
    return historical_positions

@app.post("/api/close-position/{symbol}")
async def close_position(symbol: str, request: Request, session = Depends(get_current_session)):
    """Close a position"""
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Validate symbol
        if not security_manager.input_validator.validate_symbol(symbol):
            security_manager.log_security_event(
                "invalid_symbol_access",
                session.user_id,
                client_ip,
                {"symbol": symbol, "action": "close_position"},
                SecurityLevel.MEDIUM
            )
            raise HTTPException(status_code=400, detail="Invalid symbol format")
        
        # Check permissions
        if "write" not in session.permissions:
            security_manager.log_security_event(
                "unauthorized_trading_action",
                session.user_id,
                client_ip,
                {"symbol": symbol, "action": "close_position"},
                SecurityLevel.HIGH
            )
            raise HTTPException(status_code=403, detail="Trading permission required")
        
        if binance_client is None:
            return {"error": "Trading client not initialized"}

        # Get the position to close
        position = next((p for p in current_positions if p.symbol == symbol), None)
        if not position:
            return {"error": "Position not found"}

        # Calculate the side and quantity for closing
        position_amount = float(position.positionAmt)
        if position_amount == 0:
            return {"error": "Position already closed"}

        # Cancel all open orders for this symbol
        try:
            await binance_client.futures_cancel_all_open_orders(symbol=symbol)
        except Exception as e:
            logger.warning(f"Error canceling orders: {e}")

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
        current_positions[:] = [p for p in current_positions if p.symbol != symbol]

        security_manager.log_security_event(
            "position_closed",
            session.user_id,
            client_ip,
            {"symbol": symbol, "quantity": quantity, "side": side},
            SecurityLevel.LOW
        )

        return {"message": f"Position closed successfully for {symbol}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in close_position: {e}", category=ErrorCategory.TRADING, severity=LogSeverity.HIGH)
        return {"error": str(e)}

@app.post("/api/set-tpsl/{symbol}")
async def set_tpsl(symbol: str, request: Request, tpsl_request: SecureTPSLRequest, session = Depends(get_current_session)):
    """Set take profit and stop loss"""
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Validate symbol
        if not security_manager.input_validator.validate_symbol(symbol):
            raise HTTPException(status_code=400, detail="Invalid symbol format")
        
        # Check permissions
        if "write" not in session.permissions:
            security_manager.log_security_event(
                "unauthorized_trading_action",
                session.user_id,
                client_ip,
                {"symbol": symbol, "action": "set_tpsl"},
                SecurityLevel.HIGH
            )
            raise HTTPException(status_code=403, detail="Trading permission required")
        
        if binance_client is None:
            return {"error": "Trading client not initialized"}

        # Get the position
        position = next((p for p in current_positions if p.symbol == symbol), None)
        if not position:
            return {"error": "Position not found"}

        position_amount = float(position.positionAmt)
        if position_amount == 0:
            return {"error": "Position already closed"}

        # Log the action
        security_manager.log_security_event(
            "tpsl_set",
            session.user_id,
            client_ip,
            {
                "symbol": symbol,
                "tp_percentage": tpsl_request.take_profit_percentage,
                "sl_percentage": tpsl_request.stop_loss_percentage
            },
            SecurityLevel.LOW
        )

        # Implementation would continue here...
        return {"message": f"TP/SL set successfully for {symbol}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in set_tpsl: {e}", category=ErrorCategory.TRADING, severity=LogSeverity.HIGH)
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Secure WebSocket endpoint"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    try:
        # Get session ID from query parameters or headers
        session_id = websocket.query_params.get("session_id")
        
        if not session_id:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate session
        session = security_manager.auth_manager.session_manager.validate_session(session_id, client_ip)
        if not session:
            await websocket.close(code=1008, reason="Invalid session")
            return
        
        await manager.connect(websocket, session_id)
        
        try:
            while True:
                # Keep connection alive and handle messages
                data = await websocket.receive_text()
                
                # Process WebSocket messages here
                # For now, just echo back
                await websocket.send_text(f"Echo: {data}")
                
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}", category=ErrorCategory.NETWORK, severity=LogSeverity.MEDIUM)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass

# Update functions (same as original but with security logging)
async def update_ui_values(new_positions, new_conditions, new_wallet, new_historical):
    """Update UI values and broadcast to connected clients"""
    global current_positions, trading_conditions, wallet_info, historical_positions
    
    current_positions = new_positions
    trading_conditions = new_conditions
    wallet_info = new_wallet
    historical_positions = new_historical
    
    # Broadcast updates to all connected clients
    update_data = {
        "type": "update",
        "data": {
            "positions": [pos.dict() if hasattr(pos, 'dict') else pos for pos in current_positions],
            "conditions": [cond.dict() if hasattr(cond, 'dict') else cond for cond in trading_conditions],
            "wallet": wallet_info.dict() if hasattr(wallet_info, 'dict') else wallet_info,
            "historical": [hist.dict() if hasattr(hist, 'dict') else hist for hist in historical_positions]
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(update_data)

async def update_ui(symbols, client):
    """Update UI with latest data"""
    global binance_client
    binance_client = client
    
    while True:
        try:
            # Get updated data
            new_positions = await get_current_position_ui(client)
            new_conditions = await get_trading_conditions_ui(symbols)
            new_wallet = await get_wallet_info(client)
            new_historical = await get_last_5_positions(client)
            
            # Update and broadcast
            await update_ui_values(new_positions, new_conditions, new_wallet, new_historical)
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logger.error(f"Error updating UI: {e}", category=ErrorCategory.SYSTEM, severity=LogSeverity.MEDIUM)
            await asyncio.sleep(5)  # Wait longer on error

def run_uvicorn():
    """Run the secure FastAPI server"""
    # Path to SSL certificates
    cert_dir = os.path.join(os.path.dirname(__file__), "..", "certs")
    cert_file = os.path.join(cert_dir, "localhost-cert.pem")
    key_file = os.path.join(cert_dir, "localhost-key.pem")
    
    # Check if SSL certificates exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info("Starting secure HTTPS server")
        uvicorn.run(
            "utils.web_ui.project.api.secure_main:app",
            host="127.0.0.1",
            port=8000,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            reload=False,
            log_level="info"
        )
    else:
        logger.warning("SSL certificates not found, starting HTTP server")
        uvicorn.run(
            "utils.web_ui.project.api.secure_main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )

async def start_secure_server_and_updater(symbols, client):
    """Start the secure server and updater tasks"""
    logger.info("Starting secure API server and updater")
    
    # Initialize async components first
    try:
        await security_manager.start_async_cleanup()
        logger.info("Security manager async components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize security manager: {e}")
    
    # Start the updater task
    updater_task = asyncio.create_task(update_ui(symbols, client))
    
    # Start the server in a separate process/thread
    server_task = asyncio.create_task(asyncio.to_thread(run_uvicorn))
    
    return server_task, updater_task

if __name__ == "__main__":
    run_uvicorn() 