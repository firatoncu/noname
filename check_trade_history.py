#!/usr/bin/env python3
"""
Check how many trades are available in Binance account history
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.load_config import load_config
from binance import AsyncClient

async def check_trade_history():
    """Check how many trades are available"""
    try:
        # Load config
        config = load_config()
        
        # Get API credentials
        api_key = config['api_keys']['api_key']
        api_secret = config['api_keys']['api_secret']
        testnet = config['exchange'].get('testnet', False)
        
        print(f"🔍 Checking Trade History")
        print(f"Testnet: {testnet}")
        print("=" * 40)
        
        # Create client
        client = AsyncClient(api_key, api_secret, testnet=testnet)
        
        # Check different trade limits
        limits = [100, 500, 1000, 2000]
        
        for limit in limits:
            print(f"\n📊 Fetching last {limit} trades...")
            try:
                trades = await client.futures_account_trades(limit=limit)
                print(f"   ✅ Retrieved {len(trades)} trades")
                
                if trades:
                    # Show date range
                    from datetime import datetime
                    timestamps = [trade['time'] for trade in trades]
                    oldest_ts = min(timestamps)
                    newest_ts = max(timestamps)
                    
                    oldest_date = datetime.fromtimestamp(oldest_ts / 1000)
                    newest_date = datetime.fromtimestamp(newest_ts / 1000)
                    
                    print(f"   📅 Date range:")
                    print(f"      Newest: {newest_date}")
                    print(f"      Oldest: {oldest_date}")
                    
                    # Show symbols
                    symbols = set(trade['symbol'] for trade in trades)
                    print(f"   🎯 Symbols: {sorted(symbols)}")
                    
                    # Show realized PnL trades
                    realized_trades = [t for t in trades if float(t.get('realizedPnl', 0)) != 0]
                    print(f"   💰 Trades with realized P&L: {len(realized_trades)}")
                    
                else:
                    print("   ⚠️  No trades found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        await client.close_connection()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_trade_history()) 