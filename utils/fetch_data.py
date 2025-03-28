import pandas as pd

async def binance_fetch_data(lookback_period, symbol, client, interval='1m'):
    klines = await client.futures_klines(symbol=symbol, interval=interval, limit=lookback_period)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = pd.to_numeric(df['close'])
    close_price = df['close'].iloc[-1]
    return df, close_price