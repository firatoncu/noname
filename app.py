from binance.client import Client
from utils.load_config import load_config
from utils.initial_adjustments import initial_adjustments
from utils.logging import logger_func
from src.open_position import open_position

logger = logger_func()
config = load_config()

api_config = config['api_keys']
symbol_config = config['symbols']
leverage = symbol_config['leverage']
max_open_positions = symbol_config['max_open_positions']
symbols = symbol_config['symbols']

client = Client(api_config['api_key'], api_config['secret'])
initial_adjustments(leverage, symbols, client, logger)


while True:
    open_position(max_open_positions, symbols, logger, 
                  client, leverage)