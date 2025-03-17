from src.backtesting.backtesting_strategy import futures_strategy
from src.backtesting.result_export import generate_trade_log
from src.backtesting.fetch_data import fetch_historical_data
from src.backtesting.get_input_from_user import get_inputs_for_backtest


def backtest_pipeline(client, logger):
    while True:
        try:
            start_unix_timestamp_ms, end_unix_timestamp_ms, time_interval, symbol, balance_info, leverage, fee_rate = get_inputs_for_backtest()
            df = fetch_historical_data(client, symbol, start_unix_timestamp_ms, end_unix_timestamp_ms, time_interval)
            df = futures_strategy(df, logger, leverage, fee_rate, initial_balance=balance_info)
            generate_trade_log(df, log_filename='trade_log.csv')
            input("\nPress Enter to continue...")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            input("\nPress Enter to continue...")