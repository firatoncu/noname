
import ta
from src.check_condition import check_buy_conditions, check_sell_conditions
import pandas as pd
from src.backtesting.backtest_strategies.strategy01 import check_buy_conditions, check_sell_conditions 
from src.backtesting.get_input_from_user import unix_milliseconds_to_datetime


def futures_strategy(df, logger, leverage=10, fee_rate=0.0002, initial_balance=10000):
    """
    Backtest the trading strategy using historical data.
    
    Parameters:
    - df: DataFrame with historical data (columns: 'close', etc.)
    - symbol: Trading symbol (e.g., 'BTCUSDT')
    - logger: Logger object (can be mocked or used for logging)
    - leverage: Trading leverage (default: 10)
    - fee_rate: Fee per trade as a fraction (default: 0.0002 or 0.02%)
    - initial_balance: Starting capital in USD (default: 10000)
    
    Returns:
    - df: Updated DataFrame with trading metrics
    """
    # Check if enough data is available
    histogram_lookback = 500
    if len(df) < histogram_lookback*2:
        print("Not enough data to run the strategy. Need at least 1000 candles.")
        return None

    # Initialize DataFrame columns
    df['position'] = None         # 'long', 'short', or None
    df['entry_price'] = 0.0       # Entry price of the current position
    df['quantity'] = 0.0          # Quantity in asset units
    df['unrealized_pnl'] = 0.0    # Unrealized profit/loss
    df['realized_pnl'] = 0.0      # Cumulative realized profit/loss
    df['balance'] = initial_balance  # Account balance
    df['open_time'] = df['open_time'].apply(unix_milliseconds_to_datetime)
    # Initialize trading variables
    balance = initial_balance
    realized_pnl = 0.0
    current_position = None
    quantity = 0.0
    entry_price = 0.0
    df['close'] = pd.to_numeric(df['close'])

    # Iterate from the 500th candle (index 499) onward
    for i in range(499, len(df)):
        # Get the last 500 candles up to the current candle
        df_500 = df.iloc[i-499:i+1]
        close_price = float(df.iloc[i]['close'])

        # Check buy and sell conditions using the last 500 candles
        buyAll = check_buy_conditions(df_500, logger, histogram_lookback)
        sellAll = check_sell_conditions(df_500, logger, histogram_lookback)

        # Handle existing position (TP/SL checks)
        if current_position == 'long':
            tp_price = entry_price * 1.0033  # TP: +0.33%
            sl_price = entry_price * 0.993   # SL: -0.7%
            if close_price >= tp_price or close_price <= sl_price:
                # Close long position
                pnl = (close_price - entry_price) * quantity
                notional_value = quantity * entry_price
                fee = notional_value * fee_rate  # Closing fee
                balance += pnl - fee
                realized_pnl += pnl - fee
                current_position = None
                quantity = 0.0

        elif current_position == 'short':
            tp_price = entry_price * 0.9966  # TP: -0.34%
            sl_price = entry_price * 1.007   # SL: +0.7%
            if close_price <= tp_price or close_price >= sl_price:
                # Close short position
                pnl = (entry_price - close_price) * quantity
                notional_value = quantity * entry_price
                fee = notional_value * fee_rate
                balance += pnl - fee
                realized_pnl += pnl - fee
                current_position = None
                quantity = 0.0

        # Handle new positions or position switches
        if current_position is None:
            if buyAll:
                # Open long position
                margin = balance
                notional_value = margin * leverage
                quantity = notional_value / close_price
                entry_price = close_price
                current_position = 'long'
                fee = notional_value * fee_rate
                balance -= fee
                realized_pnl -= fee
            elif sellAll:
                # Open short position
                margin = balance
                notional_value = margin * leverage
                quantity = notional_value / close_price
                entry_price = close_price
                current_position = 'short'
                fee = notional_value * fee_rate
                balance -= fee
                realized_pnl -= fee
        else:
            if current_position == 'short' and buyAll:
                profit_percentage = (entry_price - close_price) / entry_price
                if profit_percentage > 0.01:  # >1% profit to switch
                    # Close short position
                    pnl = (entry_price - close_price) * quantity
                    notional_value = quantity * entry_price
                    fee = notional_value * fee_rate
                    balance += pnl - fee
                    realized_pnl += pnl - fee
                    # Open long position
                    margin = balance
                    notional_value = margin * leverage
                    quantity = notional_value / close_price
                    entry_price = close_price
                    current_position = 'long'
                    fee = notional_value * fee_rate
                    balance -= fee
                    realized_pnl -= fee
            elif current_position == 'long' and sellAll:
                profit_percentage = (close_price - entry_price) / entry_price
                if profit_percentage > 0.01:  # >1% profit to switch
                    # Close long position
                    pnl = (close_price - entry_price) * quantity
                    notional_value = quantity * entry_price
                    fee = notional_value * fee_rate
                    balance += pnl - fee
                    realized_pnl += pnl - fee
                    # Open short position
                    margin = balance
                    notional_value = margin * leverage
                    quantity = notional_value / close_price
                    entry_price = close_price
                    current_position = 'short'
                    fee = notional_value * fee_rate
                    balance -= fee
                    realized_pnl -= fee

        # Calculate unrealized PnL
        if current_position == 'long':
            unrealized_pnl = (close_price - entry_price) * quantity
        elif current_position == 'short':
            unrealized_pnl = (entry_price - close_price) * quantity
        else:
            unrealized_pnl = 0.0

        # Update DataFrame
        df.at[i, 'position'] = current_position
        df.at[i, 'entry_price'] = entry_price if current_position else 0.0
        df.at[i, 'quantity'] = quantity if current_position else 0.0
        df.at[i, 'unrealized_pnl'] = unrealized_pnl
        df.at[i, 'realized_pnl'] = realized_pnl
        df.at[i, 'balance'] = balance

    return df