from binance.client import Client
from utils.load_config import load_config
from utils.adjust_leverage import adjust_leverage
from utils.logging import logger_func
from src.open_position import open_position
from globals import set_clean_sell_signal, set_clean_buy_signal

logger = logger_func()
config = load_config()

api_config = config['api_keys']
symbol_config = config['symbols']
leverage = symbol_config['leverage']
max_open_positions = symbol_config['max_open_positions']
symbols = symbol_config['symbols']

client = Client(api_config['api_key'], api_config['secret'])
adjust_leverage(leverage, symbols, client, logger)

# Set global variables to False at the start of the code execution
set_clean_sell_signal(False)
set_clean_buy_signal(False)

while True:
    open_position(max_open_positions, symbols, logger, 
                  client, leverage)