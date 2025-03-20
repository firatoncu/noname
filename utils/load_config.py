import yaml  # type: ignore
import os
import sys
import time

import threading
import random
from colorama import Fore, Style, init

def input_with_spinner(prompt):
    spinner_running = [True]  # using a list to allow inner function to modify the flag
    spinner_chars = ['|', '/', '-', '\\']

    def spinner():
        i = 0
        while spinner_running[0]:
            # Write prompt with spinner character appended
            sys.stdout.write('\r' + prompt + " " + spinner_chars[i % len(spinner_chars)])
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1


    spin_thread = threading.Thread(target=spinner)
    spin_thread.start()
    
    # Read user input on the same line (overwriting spinner)
    result = input('\r' + prompt + " ")
    
    spinner_running[0] = False  # signal the spinner to stop
    spin_thread.join()           # wait for spinner thread to finish
    return result.strip()

import curses
import time

def select_multiple_from_list(options, 
                              prompt="Select symbols:",
                              instructions="Use arrow keys and space to select/deselect. When done, press Enter to confirm selection."):
    selected = [False] * len(options)
    current_index = 0
    spinner_chars = ['|', '/', '-', '\\']
    spinner_index = 0
    last_time = time.time()
    spinner_delay = 0.1

    def curses_menu(stdscr):
        nonlocal current_index, spinner_index, last_time
        curses.curs_set(0)  # Hide the cursor
        stdscr.nodelay(True)  # Non-blocking mode to update spinner
        stdscr.keypad(True)   # Enable special keys

        while True:
            stdscr.clear()
            # Display prompt at the top
            stdscr.addstr(0, 0, prompt)
            # List each option with a checkbox
            for idx, option in enumerate(options):
                checkbox = "[x]" if selected[idx] else "[ ]"
                if idx == current_index:
                    stdscr.addstr(idx + 1, 0, f"{checkbox} {option}", curses.A_REVERSE)
                else:
                    stdscr.addstr(idx + 1, 0, f"{checkbox} {option}")
            # Update the spinner for the instruction text
            now = time.time()
            if now - last_time >= spinner_delay:
                spinner_index = (spinner_index + 1) % len(spinner_chars)
                last_time = now
            spinner_char = spinner_chars[spinner_index]
            # Display the instruction with spinner at the bottom
            stdscr.addstr(len(options) + 2, 0, instructions + " " + spinner_char)
            stdscr.refresh()

            try:
                key = stdscr.getch()
            except Exception:
                key = -1

            if key == -1:
                time.sleep(0.05)
                continue

            if key == curses.KEY_UP and current_index > 0:
                current_index -= 1
            elif key == curses.KEY_DOWN and current_index < len(options) - 1:
                current_index += 1
            elif key == ord(' '):
                # Toggle the selection at the current index
                selected[current_index] = not selected[current_index]
            elif key in [10, 13]:  # Enter key pressed
                break

    curses.wrapper(curses_menu)
    # Return the list of options that were selected
    return [option for option, sel in zip(options, selected) if sel]

from typing import List, Dict, Optional
def get_top_n_pairs_by_vol(n: int = 10) -> List[str]:
    """
    Retrieve the top N USDT trading pairs from Binance based on 24-hour trading volume.

    Args:
        n (int): Number of top pairs to return. Defaults to 10.

    Returns:
        List[str]: A list of the top N USDT pair symbols (e.g., ['BTCUSDT', 'ETHUSDT']).

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the response format is invalid or insufficient data is available.
    """
    # Define the API endpoint
    url = "https://api.coingecko.com/api/v3/exchanges/binance/tickers"
    import requests
    
    try:
        # Fetch ticker data from CoinGecko
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        # Validate response structure
        if not isinstance(data, dict) or 'tickers' not in data:
            raise ValueError("Invalid API response format: 'tickers' key missing")

        # Filter for USDT pairs and extract relevant data
        usdt_pairs = [
            {
                'symbol': f"{ticker['base']}USDT",
                'volume_usd': float(ticker['converted_volume'].get('usd', 0))
            }
            for ticker in data['tickers']
            if ticker.get('target') == 'USDT'
            and 'base' in ticker
            and 'converted_volume' in ticker
        ]

        # Sort by 24-hour USD volume in descending order
        sorted_pairs = sorted(usdt_pairs, key=lambda x: x['volume_usd'], reverse=True)

        # Handle case where fewer pairs are available than requested
        if not sorted_pairs:
            raise ValueError("No USDT pairs found in the response")
        available_pairs = min(n, len(sorted_pairs))
        if available_pairs < n:
            print(f"Warning: Only {available_pairs} USDT pairs available, less than requested {n}")

        # Extract the top N symbols
        top_pairs = [pair['symbol'] for pair in sorted_pairs[:available_pairs]]
        return top_pairs
    
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch data from CoinGecko: {e}")
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Error processing API response: {e}")

def load_config(file_path='config.yml'):
    os.system("cls" if os.name == "nt" else "clear")
    # Determine the base path (script dir or executable dir)
    if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
        base_path = os.path.dirname(sys.executable)
    else:  # Running as a Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, file_path)

    try:
        with open(full_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    except FileNotFoundError:
        print(f"\nConfig file '{full_path}' not found. Let's create a new one.\n")
        # Initialize config with defaults
        config = {
            'symbols': {},
            'capital_tbu': None  # Default to using full balance
        }
        # Default values
        default_symbols = "BTCUSDT,ETHUSDT"
        default_leverage = 3
        default_max_positions = 2

        config['symbols']['symbols'] = default_symbols.split(',')
        config['symbols']['leverage'] = default_leverage
        config['symbols']['max_open_positions'] = default_max_positions
        
        colors = [
        Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA,
        Fore.CYAN, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
        Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.WHITE
        ]

    # Choose a random color
        random_color = random.choice(colors)
        # Menu loop for configuration
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            print(f"""{random_color}{Style.BRIGHT}
        ______                             ______             ___ _                                        
       / __   |                           / _____)           / __|_)                       _               
 ____ | | //| |____   ____ ____   ____   | /      ___  ____ | |__ _  ____ _   _  ____ ____| |_  ___   ____ 
|  _ \| |// | |  _ \ / _  |    \ / _  )  | |     / _ \|  _ \|  __) |/ _  | | | |/ ___) _  |  _)/ _ \ / ___)
| | | |  /__| | | | ( ( | | | | ( (/ /   | \____| |_| | | | | |  | ( ( | | |_| | |  ( ( | | |_| |_| | |    
|_| |_|\_____/|_| |_|\_||_|_|_|_|\____)   \______)___/|_| |_|_|  |_|\_|| |\____|_|   \_||_|\___)___/|_|    
                                                                   (_____|                                 
{Style.RESET_ALL}""")
            print(f"\n\n{Style.BRIGHT}Welcome to the n0name Configurator \n\n  {Style.RESET_ALL}")
            print("Here you can define your trading configuration.\n")
            print("- Trading Symbols\n- Leverage\n- Capital to be used\n- Number of Max Open Positions.\n")
            print("Here is a default configuration:")
            print(f"1. Symbols: {', '.join(config['symbols']['symbols'])}")
            print(f"2. Leverage: {config['symbols']['leverage']}")
            cap_display = "Full balance" if config['capital_tbu'] is None else config['capital_tbu']
            print(f"3. Capital to be used: {cap_display}")
            print(f"4. Max Open Positions: {config['symbols']['max_open_positions']}")
            print("5. Save and Continue")
            print("6. Exit\n")

            choice = input_with_spinner("You can configure any parameter (2 for Leverage for example) as you want or press Enter to start from the beginning ")
            # choice = input("You can configure any parameter (2 for Leverage for example) as you want or press Enter to start from the beginning.").strip()

            if choice == "1":
                predefined_symbols = get_top_n_pairs_by_vol(n=10)
                symbols_input = select_multiple_from_list(predefined_symbols)
                if not symbols_input:
                    print("No symbols entered, defaulting to BTCUSDT,ETHUSDT")
                    symbols_input = default_symbols
                print(symbols_input)
                # config['symbols']['symbols'] = [s.strip() for s in symbols_input.split(',')]
                config['symbols']['symbols'] = [s.strip() for s in symbols_input]

                time.sleep(1)

            elif choice == "2":
                lev = input("\nEnter leverage (e.g., 3): ").strip()
                if lev.isdigit():
                    config['symbols']['leverage'] = int(lev)
                else:
                    print("Invalid input. Using default value.")
                    config['symbols']['leverage'] = default_leverage
                time.sleep(1)

            elif choice == "3":
                cap = input("\nEnter capital to be used (leave blank to use the full balance): ").strip()
                if cap == "":
                    config['capital_tbu'] = None
                    print("Using full balance..")
                else:
                    try:
                        config['capital_tbu'] = float(cap)
                    except ValueError:
                        print("Invalid input. Using full balance.")
                        config['capital_tbu'] = None
                time.sleep(1)

            elif choice == "4":
                pos = input("\nEnter max open positions (e.g., 2): ").strip()
                if pos.isdigit():
                    config['symbols']['max_open_positions'] = int(pos)
                else:
                    print("Invalid input. Using default value.")
                    config['symbols']['max_open_positions'] = default_max_positions
                time.sleep(1)

            elif choice == "5":
                confirm = input("\nSave configuration? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    try:
                        with open(full_path, 'w') as file:
                            yaml.safe_dump(config, file, default_flow_style=False)
                        print(f"\nNew config file created at '{full_path}'")
                        time.sleep(1)
                        return config
                    except Exception as e:
                        print(f"Error saving new config file: {e}")
                        time.sleep(1)
                        continue
                else:
                    print("Configuration not saved. Returning to menu...")
                    time.sleep(1)

            elif choice == "6":
                print("Exiting configuration setup.")
                sys.exit(0)

            else:
                print("Invalid option. Please try again.")
                time.sleep(1)

    except yaml.YAMLError as e:
        print(f"Error parsing YAML file (delete the config file and n0name will create a new one for you): {e}")
        return None
