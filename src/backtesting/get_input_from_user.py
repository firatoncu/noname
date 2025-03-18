from datetime import datetime
import pytz  # Library for timezone handling
from utils.globals import set_user_time_zone, get_user_time_zone
import random
from colorama import Fore, Style, init
import os

init()

# List of timezones with their major cities
TIMEZONES = {
    1: ("UTC+3", ["Istanbul", "Athens"], "Etc/GMT-3"),
    2: ("UTC+1", ["Berlin", "Paris"], "Etc/GMT-1"),
    3: ("UTC-5", ["New York", "Toronto"], "Etc/GMT+5"),
    4: ("UTC+0", ["London", "Dublin"], "Etc/GMT"),
    5: ("UTC+9", ["Tokyo", "Seoul"], "Asia/Tokyo"),
    6: ("UTC-8", ["Los Angeles", "San Francisco"], "Etc/GMT+8"),
}

VALID_INTERVALS = {
    '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
}

VALID_SYMBOLS = {
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'SOLUSDT', 'UNIUSDT', 'LTCUSDT', 'SUIUSDT', 'LINKUSDT', 'MATICUSDT', 'ICPUSDT', 'ETCUSDT', 'VETUSDT', 'FILUSDT', 'TRXUSDT', 'XLMUSDT', 'SHIBUSDT', 'EOSUSDT', 'THETAUSDT', 'XMRUSDT', 'AAVEUSDT', 'NEOUSDT', 'ATOMUSDT', 'XTZUSDT', 'ALGOUSDT', 'MKRUSDT', 'CROUSDT', 'BCHUSDT', 'COMPUSDT', 'BSVUSDT', 'HTUSDT', 'WAVESUSDT'
}

def get_user_intervals():
    """Get the user's interval selection."""
    while True:
        try:
            interval = input("\nEnter the interval (e.g., '1h', '4h'): ")
            if interval in VALID_INTERVALS:
                return interval
            else:
                print("Invalid interval. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid interval.")

def get_user_symbol():
    """Get the user's symbol selection."""
    while True:
        try:
            symbol = input("\nEnter the symbol value (e.g., 'BTCUSDT'): ")
            symbol = symbol.upper()
            if symbol in VALID_SYMBOLS:
                return symbol
            else:
                print(f"Invalid symbols: {symbol}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter valid symbols.")

def get_balance_info():
    """Get the user's symbol selection."""
    while True:
        try:
            balance_info = input("\nEnter the Starting Balance value (e.g., 1000): ") or -999
            if balance_info == -999:
                print("No balance entered, defaulting to $1000")
                return 1000
            elif int(balance_info) >= 50 and int(balance_info) <= 1000000:
                print("Starting Balance set to: " + "$" + str(balance_info))
                return int(balance_info)
            else:
                print(f"Invalid Balance value {balance_info}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter valid Balance value.")

def get_leverage_info():
    """Get the user's symbol selection."""
    while True:
        try:
            leverage = input("\nEnter the leverage value (e.g., 5): ") or -999
            if leverage == -999:
                print("No leverage entered, defaulting to 5")
                return 5
            elif int(leverage) >= 0 and int(leverage) <= 125:
                print("Leverage set to: ", leverage)
                return int(leverage)
            else:
                print(f"Invalid Leverage value {leverage}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter valid leverage value.")

def get_fee_rate():
    """Get the user's symbol selection."""
    while True:
        try:
            fee_rate = input("\nEnter the fee rate value (default value is 0.0002, leave empty for default): ") or -999
            if fee_rate == -999:
                print("No fee rate entered, defaulting to 0.0002")
                return 0.0002
            elif float(fee_rate) >= 0:
                print("Fee rate set to: ", fee_rate)
                return float(fee_rate)
            else:
                print(f"Invalid fee rate value {fee_rate}. Please try again.")
        except ValueError:
            print("Invalid input. Please enter valid fee rate value.")

def print_welcome_message():
    os.system("cls" if os.name == "nt" else "clear") 
            # List of available foreground colors (excluding RESET)
    colors = [
        Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA,
        Fore.CYAN, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.WHITE
    ]

    # Choose a random color
    random_color = random.choice(colors)
    print(f"""{random_color}{Style.BRIGHT}

        ______                            _                 _                         _                _                
       / __   |                          | |               | |    _              _   (_)              | |          _    
 ____ | | //| |____   ____ ____   ____   | | _   ____  ____| |  _| |_  ____  ___| |_  _ ____   ____   | | _   ___ | |_  
|  _ \| |// | |  _ \ / _  |    \ / _  )  | || \ / _  |/ ___) | / )  _)/ _  )/___)  _)| |  _ \ / _  |  | || \ / _ \|  _) 
| | | |  /__| | | | ( ( | | | | ( (/ /   | |_) | ( | ( (___| |< (| |_( (/ /|___ | |__| | | | ( ( | |  | |_) ) |_| | |__ 
|_| |_|\_____/|_| |_|\_||_|_|_|_|\____)  |____/ \_||_|\____)_| \_)\___)____|___/ \___)_|_| |_|\_|| |  |____/ \___/ \___)
                                                                                             (_____|                    

          {Style.RESET_ALL}""")

    print(f"{Style.BRIGHT}Welcome to the n0name backtesting tool!{Style.RESET_ALL}")
    print("This tool allows you to backtest your trading strategies using historical data.")
    print("You can select a timezone, start and end date times, interval, and symbol to begin.")
    print("Let's get started!\n\n")

def display_timezones():
    """Display available timezones to the user."""
    print("\nSelect a timezone:")
    for key, (offset, cities, _) in TIMEZONES.items():
        print(f"{key} - {offset} ({', '.join(cities)})")

def get_user_timezone():
    """Get the user's timezone selection."""
    while True:
        try:
            choice = int(input("Enter the number of your timezone: "))
            if choice in TIMEZONES:
                set_user_time_zone(TIMEZONES[choice][2])  # Set the timezone
                print("Timezone set to: ", TIMEZONES[choice][1])
                return TIMEZONES[choice][2]  # Return the Capital name
                
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_user_datetime(input_str):
    """Get the user's datetime input in the specified format."""
    while True:
        try:
            datetime_str = input(input_str)
            dt = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M:%S")
            return dt
        except ValueError:
            print("Invalid format. Please try again.")

def datetime_to_unix_milliseconds(dt):
    """Convert a timezone-aware datetime to Unix timestamp in milliseconds."""
    # Attach the selected timezone to the datetime
    timezone = get_user_time_zone()
    tz = pytz.timezone(timezone)
    dt = tz.localize(dt)

    # Convert to Unix timestamp in milliseconds
    unix_timestamp_ms = int(dt.timestamp() * 1000)
    return unix_timestamp_ms

def unix_milliseconds_to_datetime(unix_timestamp_ms):
    """
    Convert a Unix timestamp in milliseconds to a timezone-aware datetime object.

    :param unix_timestamp_ms: Unix timestamp in milliseconds.
    :param timezone: Desired timezone .
    :return: Timezone-aware datetime object.
    """
    # Convert milliseconds to seconds
    unix_timestamp_seconds = int(unix_timestamp_ms) / 1000
    timezone = get_user_time_zone()
    # Convert to datetime (UTC)
    dt = datetime.fromtimestamp(unix_timestamp_seconds)

    # Attach the desired timezone
    tz = pytz.timezone(timezone)
    dt = dt.replace(tzinfo=pytz.utc).astimezone(tz)
    dt = dt.strftime('%Y-%m-%d %H:%M:%S')

    return dt

def get_inputs_for_backtest():

    print_welcome_message()
    # Display timezones
    display_timezones()
    
    # Get user's timezone selection
    get_user_timezone()
    
    # Get user's datetime input
    print("\nEnter the start and end date times for the backtest: (eg. 01-01-2021 00:00:00)")
    start_datetime = get_user_datetime("Starting Date Time :") 
    end_datetime   = get_user_datetime("Ending Date Time   :") 

    # Convert to Unix timestamp in milliseconds
    start_unix_timestamp_ms = datetime_to_unix_milliseconds(start_datetime)
    end_unix_timestamp_ms = datetime_to_unix_milliseconds(end_datetime)

    time_interval = get_user_intervals()

    symbol = get_user_symbol()

    leverage = get_leverage_info()
    balance_info = get_balance_info()
    fee_rate = get_fee_rate()
    
    return start_unix_timestamp_ms, end_unix_timestamp_ms, time_interval, symbol, balance_info, leverage, fee_rate