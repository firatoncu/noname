from utils.globals import get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc, get_funding_flag
import asyncio

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
        trading_condition = {
            'symbol': symbol,
            'fundingPeriod': funding_period,
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

