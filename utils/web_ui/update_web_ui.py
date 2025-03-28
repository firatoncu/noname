from utils.globals import get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc, get_funding_flag, get_trend_signal
import asyncio
from datetime import datetime , timedelta
from typing import Literal, List, Dict, Any, Tuple
from pydantic import BaseModel
from src.backtesting.get_input_from_user import unix_milliseconds_to_datetime

def get_conditions_for_symbol_ui(symbol) -> tuple[dict, dict]:
    buy_conditions = {
        'condA': get_buyconda(symbol),
        'condB': get_buycondb(symbol),
        'condC': get_buycondc(symbol)
    }
    sell_conditions = {
        'condA': get_sellconda(symbol),
        'condB': get_sellcondb(symbol),
        'condC': get_sellcondc(symbol)
    }
    return buy_conditions, sell_conditions


async def get_trading_conditions_ui(symbols):
    trading_conditions = []
    for symbol in symbols:
        buy_conditions, sell_conditions = get_conditions_for_symbol_ui(symbol)
        funding_period = get_funding_flag(symbol)
        trending_condition = get_trend_signal(symbol)
        trading_condition = {
            'symbol': symbol,
            'fundingPeriod': funding_period,
            'trendingCondition': trending_condition,
            'buyConditions': buy_conditions,
            'sellConditions': sell_conditions
        }
        trading_conditions.append(trading_condition)
    return trading_conditions


async def get_current_position_ui(client):
    if await client.futures_position_information():
        position = await client.futures_position_information()
        pos = position[0]

        current_position = [{
                'symbol': pos['symbol'],
                'positionAmt': pos['positionAmt'],
                'notional': pos['notional'],
                'unRealizedProfit': pos['unRealizedProfit'],
                'entryPrice': pos['entryPrice'],
                'markPrice': pos['markPrice']
            }]
        
    else:
        current_position = []
    
    return current_position


# Your data structure
class HistoricalPosition(BaseModel):
    symbol: str
    entryPrice: str   # Price from the first open trade in the position
    exitPrice: str    # Price from the closing trade (the most recent closed trade)
    profit: str       # Sum of realizedPnL from the closed trades
    amount: str       # Total USDT value from the open orders (entry value sum)
    side: Literal['LONG', 'SHORT']
    openedAt: str     # Timestamp (ms) of the opening trade
    closedAt: str     # Timestamp (ms) of the closing trade

def extract_position(trades: List[Dict[str, Any]], start_index: int) -> Tuple[HistoricalPosition, int]:
    n = len(trades)
    i = start_index

    # Step 1: Skip open trades until a closed trade is found.
    while i < n and float(trades[i].get('realizedPnl', 0)) == 0:
        i += 1
    if i >= n:
        raise ValueError(f"No closed trade found starting at index {start_index}")
    
    closing_trade = trades[i]
    symbol = closing_trade['symbol']
    # Determine position side: if qty < 0 then closing a LONG; if qty > 0 then closing a SHORT.
    position_side = "LONG" if str(closing_trade['side']) == "SELL" else "SHORT"
    exit_price = closing_trade['price']
    closed_at = unix_milliseconds_to_datetime(closing_trade['time'])
    pnl_sum = float(closing_trade.get('realizedPnl', 0))
    i += 1

    # Step 2: Sum subsequent closed trades for the same symbol and side.
    while i < n:
        trade = trades[i]
        if trade['symbol'] != symbol:
            break
        pnl_val = float(trade.get('realizedPnl', 0))
        # Determine trade's closed side using the same rule.
        #trade_side = "LONG" if str(trade['side']) == "SELL" else "SHORT"
        if pnl_val != 0 :
            pnl_sum += pnl_val
            i += 1
        else:
            break

    # Step 3: Now sum open trades (realizedPnl == 0) that mark the beginning of the position.
    entry_value_sum = 0.0  # Sum of USDT amounts for open orders.
    entry_price = None     # Price from the first open order (this will be our entry price).
    while i < n:
        trade = trades[i]
        if trade['symbol'] != symbol or float(trade.get('realizedPnl', 0)) != 0:
            break
        if entry_price is None:
            entry_price = trade['price']  # Use the first encountered open trade's price.
            opened_at = unix_milliseconds_to_datetime(trade['time'])
        # Assume USDT amount is price * abs(qty)
        entry_value_sum += float(trade['price']) * abs(float(trade['qty']))

        i += 1
    if entry_price is None:
        # If no open trade is found to mark the position's beginning, we can't compute the entry price.
        raise ValueError("No open trade (realizedPnl==0) found for the beginning of the position.")
    
    # Create the HistoricalPosition
    pos = HistoricalPosition(
        symbol=symbol,
        entryPrice=str(entry_price),
        exitPrice=str(exit_price),
        profit=str(pnl_sum),
        amount=str(entry_value_sum),
        side=position_side,
        openedAt=str(opened_at), 
        closedAt=str(closed_at)
    )
    return pos, i

async def get_last_5_positions(client) -> List[HistoricalPosition]:
    try:
        # Retrieve a sufficiently large batch of trades
        trades = await client.futures_account_trades(limit=500)
        # Sort trades descending by time (most recent first)
        trades.sort(key=lambda t: t['time'], reverse=True)
        positions = []
        i = 0
        n = len(trades)
        # Extract positions until we have 5 or we run out of trades.
        while i < n and len(positions) < 5:
            try:
                pos, new_index = extract_position(trades, i)
                positions.append(pos)
                # Update index to continue after the position's records.
                i = new_index
            except ValueError as e:
                # If extraction fails, break out.
                print("Extraction stopped:", e)
                break
        return positions
    finally:
        await asyncio.sleep(2)

# Define the WalletInfo model
class WalletInfo(BaseModel):
    totalBalance: str
    availableBalance: str
    unrealizedPnL: str
    dailyPnL: str
    weeklyPnL: str
    marginRatio: str

# Async function to get wallet information
async def get_wallet_info(client):
    # Initialize AsyncClient    

    # Fetch Futures account information
    account_info = await client.futures_account()
    
# Fetch income history for daily and weekly PnL
    now = datetime.utcnow()
    daily_start = int((now - timedelta(days=1)).timestamp() * 1000)
    weekly_start = int((now - timedelta(days=7)).timestamp() * 1000)
    
    daily_income = await client.futures_income_history(startTime=daily_start, limit=1000)
    weekly_income = await client.futures_income_history(startTime=weekly_start, limit=1000)
    
    # Extract data from account_info
    total_balance = float(account_info['totalWalletBalance'])  # Convert to float for calculation
    available_balance = account_info['availableBalance']
    unrealized_pnl = account_info['totalUnrealizedProfit']
    
    # Calculate daily PnL from income history
    daily_pnl = sum(float(income['income']) for income in daily_income if income['incomeType'] != 'TRANSFER')
    
    # Calculate daily profit margin as a percentage
    if total_balance > 0:  # Avoid division by zero
        daily_margin = (daily_pnl / total_balance) * 100  # Percentage return on total balance
    else:
        daily_margin = 0.0  # Default to 0 if no balance

    weekly_pnl = sum(float(income['income']) for income in weekly_income if income['incomeType'] != 'TRANSFER')
    
    # Create WalletInfo object
    wallet_info = WalletInfo(
        totalBalance=str(total_balance),
        availableBalance=str(available_balance),
        unrealizedPnL=str(unrealized_pnl),
        dailyPnL=str(daily_pnl),
        weeklyPnL=str(weekly_pnl),
        marginRatio=str(daily_margin)
    )
    
    return wallet_info.dict()