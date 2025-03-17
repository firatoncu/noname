from src.backtesting.backtesting_strategy import futures_strategy
from src.backtesting.result_export import generate_trade_log
from src.backtesting.fetch_data import fetch_historical_data
from src.backtesting.get_input_from_user import get_inputs_for_backtest


def backtest_pipeline(client, logger):
    start_unix_timestamp_ms, end_unix_timestamp_ms, time_interval, symbol = get_inputs_for_backtest()
    df = fetch_historical_data(client, symbol, start_unix_timestamp_ms, end_unix_timestamp_ms, time_interval)
    df = futures_strategy(df, logger, leverage=10, fee_rate=0.0002, initial_balance=10000)
    generate_trade_log(df, log_filename='trade_log.csv')