import time
from binance.exceptions import BinanceAPIException
import pandas as pd

def fetch_historical_data(client, symbol, start_time_ms, end_time_ms, interval):
    """
    Fetches historical klines data from Binance Futures for multiple symbol within a specified time range.
    
    Parameters:
        client (binance.Client): Initialized Binance client.
        symbol: Trading symbol (e.g.,'BTCUSDT').
        start_time_ms (int): Start timestamp in milliseconds.
        end_time_ms (int): End timestamp in milliseconds.
        interval (str): Kline interval (e.g., '1h', '4h').
    
    Returns:
        dict: Dictionary with symbol as key and lists of formatted klines as values.
    
    Raises:
        ValueError: For invalid input parameters.
    """
    # Validate interval
    valid_intervals = {'1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'}
    
    if interval not in valid_intervals:
        raise ValueError(f"Invalid interval: {interval}. Valid intervals: {', '.join(valid_intervals)}")
    
    # Validate time range
    if start_time_ms > end_time_ms:
        raise ValueError("Start time must be before end time.")
    
    
    symbol = symbol.strip().upper()
    data = []
    current_start = start_time_ms
    
    while current_start <= end_time_ms:
        retries = 3
        success = False
        klines = []
        
        # Attempt to fetch data with retries for rate limits
        while retries > 0 and not success:
            try:
                klines = client.futures_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=current_start,
                    endTime=end_time_ms,
                    limit=1000
                )
                success = True
            except BinanceAPIException as e:
                if e.code == -1121:  # Invalid symbol
                    print(f"Invalid symbol {symbol}. Skipping.")
                    retries = 0
                    break
                elif e.status_code == 429:  # Rate limit exceeded
                    retries -= 1
                    print(f"Rate limit exceeded for {symbol}. Retries left: {retries}")
                    time.sleep(10)
                else:
                    print(f"API error for {symbol}: {e}")
                    retries = 0
                    break
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                retries = 0
                break
        
        if not success:
            print(f"Failed to fetch data for {symbol} after retries.")
            break
        
        if not klines:
            break  # No more data available
        
        # Format klines data
        formatted_klines = [{
            'open_time': k[0],
            'open': k[1],
            'high': k[2],
            'low': k[3],
            'close': k[4],
            'volume': k[5]
        } for k in klines]
        
        data.extend(formatted_klines)
        
        # Update pagination parameters
        last_open_time = klines[-1][0]
        if last_open_time >= end_time_ms:
            break  # Reached end of requested time range
        
        current_start = last_open_time + 1  # Move to next time interval
    
  
    data = pd.DataFrame(data)
    return data