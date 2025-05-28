#!/usr/bin/env python3
"""
Account Balance Checker

This script checks your Binance futures account balance and suggests
appropriate capital settings to avoid margin insufficient errors.
"""

import asyncio
import sys
from binance import AsyncClient
from binance.exceptions import BinanceAPIException

async def check_account_balance():
    """Check account balance and suggest capital settings"""
    
    # API credentials from config
    api_key = "QhTibgCwZjaDl01g37XpRKtro2qL7cgSunrXndfnazt9KZ0Nbcno0FPrV9Ja0hQ9"
    api_secret = "qDJAb8xpevCUjdUXrKr3XjmizCZDgNI0Oz8fkzN7qgyBqcGWrMoGLygL5iSxFhEz"
    
    try:
        print("🔍 Checking Binance Futures account balance...")
        
        # Create client
        client = await AsyncClient.create(api_key, api_secret)
        
        # Get account information
        account_info = await client.futures_account()
        
        print("\n📊 Account Balance Information:")
        print("=" * 50)
        
        total_wallet_balance = 0
        available_balance = 0
        
        for asset in account_info['assets']:
            wallet_balance = float(asset['walletBalance'])
            available = float(asset['availableBalance'])
            
            if wallet_balance > 0:
                print(f"{asset['asset']}: {wallet_balance:.4f} (Available: {available:.4f})")
                if asset['asset'] == 'USDT':
                    total_wallet_balance = wallet_balance
                    available_balance = available
        
        print("=" * 50)
        
        if total_wallet_balance > 0:
            print(f"\n💰 USDT Balance: {total_wallet_balance:.2f}")
            print(f"💰 Available USDT: {available_balance:.2f}")
            
            # Calculate safe capital amounts
            safe_capital_conservative = available_balance * 0.1  # 10% of available
            safe_capital_moderate = available_balance * 0.2     # 20% of available
            safe_capital_aggressive = available_balance * 0.5   # 50% of available
            
            print(f"\n📈 Suggested Capital Settings:")
            print(f"Conservative (10%): {safe_capital_conservative:.2f} USDT")
            print(f"Moderate (20%):    {safe_capital_moderate:.2f} USDT")
            print(f"Aggressive (50%):  {safe_capital_aggressive:.2f} USDT")
            
            print(f"\n⚠️  Current config capital: 50.0 USDT")
            
            if available_balance < 50:
                print(f"❌ WARNING: Your available balance ({available_balance:.2f}) is less than configured capital (50.0)")
                print(f"💡 Recommended: Set capital_tbu to {safe_capital_conservative:.2f} or lower")
            else:
                print(f"✅ Your current capital setting (50.0) should work fine!")
        else:
            print("❌ No USDT balance found in futures account")
            print("💡 Please deposit USDT to your futures account first")
        
        # Get position information
        positions = await client.futures_position_information()
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        if open_positions:
            print(f"\n📍 Current Open Positions: {len(open_positions)}")
            for pos in open_positions:
                print(f"  {pos['symbol']}: {pos['positionAmt']} (PnL: {pos['unRealizedProfit']})")
        else:
            print(f"\n📍 No open positions")
        
        await client.close_connection()
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.message}")
        if e.code == -2019:
            print("💡 This is the 'Margin is insufficient' error")
            print("💡 Solution: Reduce capital_tbu in config.yml")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_account_balance()) 