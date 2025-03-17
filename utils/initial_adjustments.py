from utils.globals import set_clean_sell_signal, set_clean_buy_signal, set_capital_tbu
import asyncio
from colorama import Fore, Style, init
import random
from utils.logging import logger_func
from utils.cursor_movement import clean_line
logger = logger_func()
import os

# Colorama'yı başlat


async def initial_adjustments(leverage, symbols, capital_tbu, client, error_logger):
    try:
        init(autoreset=True)
        for symbol in symbols:
            set_clean_sell_signal(False, symbol)
            set_clean_buy_signal(False, symbol)
            if capital_tbu == -999:
                set_capital_tbu(None)
            else:
                set_capital_tbu(capital_tbu)
            await client.futures_change_leverage(symbol=symbol, leverage=leverage)

        # List of available foreground colors (excluding RESET)
        colors = [
            Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA,
            Fore.CYAN, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
            Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.WHITE
        ]

        # Choose a random color
        random_color = random.choice(colors)
        os.system("cls" if os.name == "nt" else "clear") 
        print(f"""{random_color}{Style.BRIGHT}
    
        ______                                                _ _                _                
       / __   |                           _                  | (_)              | |          _    
 ____ | | //| |____   ____ ____   ____   | |_   ____ ____  _ | |_ ____   ____   | | _   ___ | |_  
|  _ \| |// | |  _ \ / _  |    \ / _  )  |  _) / ___) _  |/ || | |  _ \ / _  |  | || \ / _ \|  _) 
| | | |  /__| | | | ( ( | | | | ( (/ /   | |__| |  ( ( | ( (_| | | | | ( ( | |  | |_) ) |_| | |__ 
|_| |_|\_____/|_| |_|\_||_|_|_|_|\____)   \___)_|   \_||_|\____|_|_| |_|\_|| |  |____/ \___/ \___)
                                                                       (_____|                    

          {Style.RESET_ALL}""")
        logger.info("Starting the bot...")
        await asyncio.sleep(3)  # Prevent tight looping; adjust as needed
        logger.info("Initial adjustments completed, starting main loop...")
        await asyncio.sleep(1)  # Prevent tight looping; adjust as needed
        logger.info(f"Current Crypto Pairs: {symbols}")

        print(f"""

{Fore.WHITE}{Style.BRIGHT}Trading Strategy Explanation:{Style.RESET_ALL}

{Fore.LIGHTCYAN_EX}- {Style.BRIGHT}Buy/Sell Condition 1: MACD Histogram Breakout ({Style.DIM}`last500_histogram_check`{Style.NORMAL}):{Style.RESET_ALL} 
  This checks the last 500 MACD histogram values to identify strong momentum shifts.
  {Style.BRIGHT}A buy signal occurs{Style.RESET_ALL} if the latest positive histogram value exceeds the {Style.BRIGHT}85th percentile{Style.RESET_ALL} of past values.
  {Style.BRIGHT}A sell signal occurs{Style.RESET_ALL} if the latest negative histogram value is below the {Style.BRIGHT}85th percentile{Style.RESET_ALL} (absolute).

{Fore.LIGHTBLUE_EX}- {Style.BRIGHT}Buy/Sell Condition 2: Fibonacci Retracement Confirmation ({Style.DIM}`last500_fibo_check`{Style.NORMAL}):{Style.RESET_ALL} 
  This checks if price movements align with key Fibonacci levels.
  {Style.BRIGHT}A buy signal occurs{Style.RESET_ALL} when price breaks above the {Style.BRIGHT}78.6% retracement level{Style.RESET_ALL}, with a significant gap to the {Style.BRIGHT}61.8% level{Style.RESET_ALL}.
  {Style.BRIGHT}A sell signal occurs{Style.RESET_ALL} when price falls below the {Style.BRIGHT}23.6% level{Style.RESET_ALL}, with a significant gap to the {Style.BRIGHT}38.2% level{Style.RESET_ALL}.

{Fore.LIGHTMAGENTA_EX}- {Style.BRIGHT}Buy/Sell Condition 3: MACD Signal Line Crossover ({Style.DIM}`signal_cleaner`{Style.NORMAL}):{Style.RESET_ALL} 
  This ensures clean buy or sell signals using MACD crossovers.
  {Style.BRIGHT}A buy signal is triggered{Style.RESET_ALL} when the MACD line crosses from {Style.BRIGHT}negative to positive{Style.RESET_ALL}.
  {Style.BRIGHT}A sell signal occurs{Style.RESET_ALL} when it crosses from {Style.BRIGHT}positive to negative{Style.RESET_ALL}.
                    """)

        status_lines_count = (len(symbols) * 5) + 2
        for _ in range(status_lines_count):
            print(" ") 


    except Exception as e:
        error_logger.error(f"Initial adjustments failed: {e}")