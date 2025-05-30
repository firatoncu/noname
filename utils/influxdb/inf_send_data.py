try:
    from influxdb import InfluxDBClient as OldInfluxDBClient
    OLD_INFLUXDB_AVAILABLE = True
except ImportError:
    OLD_INFLUXDB_AVAILABLE = False

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    NEW_INFLUXDB_AVAILABLE = True
except ImportError:
    NEW_INFLUXDB_AVAILABLE = False

from utils.enhanced_logging import get_logger
from datetime import datetime
import pytz
from utils.globals import set_last_timestamp, get_last_timestamp, get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc
import asyncio

# InfluxDB client - only create if available
client = None
if OLD_INFLUXDB_AVAILABLE:
    try:
        client = OldInfluxDBClient(host="localhost", port=8086, database="n0namedb")
    except Exception:
        client = None

# Gerçek zamanlı veri yazma fonksiyonu
async def write_live_data(last_candle, symbol):
    # Initialize logger inside the function
    logger = get_logger()

    try:
        if not OLD_INFLUXDB_AVAILABLE:
            logger.debug("InfluxDB not available, skipping data write")
            return
            
        timestamp = last_candle['timestamp']
        open_price = last_candle['open']
        high_price = last_candle['high']
        low_price = last_candle['low']
        close_price = last_candle['close']
        volume = last_candle['volume']

        # InfluxDB'ye veri yaz
        json_body = [
            {
                "measurement": symbol,
                "time": timestamp,
                "fields": {
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                },
            }
        ]
        client = OldInfluxDBClient(host="localhost", port=8086, database="n0namedb")
        client.write_points(json_body)

    except Exception as e:
        logger.error(f"Error in writing live data: {e}")
        return
    
async def write_live_conditions(timestamp, symbol):
    # Initialize logger inside the function
    logger = get_logger()

    try:
        if not OLD_INFLUXDB_AVAILABLE:
            logger.debug("InfluxDB not available, skipping conditions write")
            return
            
        timestamp = timestamp/1000
        utc_time = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        tr_timezone = pytz.timezone("Europe/Istanbul")
        timestamp = utc_time.astimezone(tr_timezone)
        buycond1 = get_buyconda(symbol)
        buycond2 = get_buycondb(symbol)
        buycond3 = get_buycondc(symbol)
        sellcond1 = get_sellconda(symbol)
        sellcond2 = get_sellcondb(symbol)
        sellcond3 = get_sellcondc(symbol)

        # InfluxDB'ye veri yaz
        json_body = [
            {
                "measurement": symbol,
                "time": timestamp,
                "fields": {
                    "buycond1": buycond1,
                    "buycond2": buycond2,
                    "buycond3": buycond3,
                    "sellcond1": sellcond1,
                    "sellcond2": sellcond2,
                    "sellcond3": sellcond3,
                },
            }
        ]
        client = OldInfluxDBClient(host="localhost", port=8086, database="n0namedb")
        client.write_points(json_body)

    except Exception as e:
        logger.error(f"Error in writing live data: {e}")
        return
    
async def data_writer(df, symbol):
    if get_last_timestamp(symbol) == 0:
        set_last_timestamp(df['timestamp'].iloc[-1], symbol)

    if df['timestamp'].iloc[-1] != get_last_timestamp(symbol):
        last_candle = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time']].iloc[-1]
        await write_live_data(last_candle, symbol)
        set_last_timestamp(df['timestamp'].iloc[-1], symbol)

async def condition_writer(df, symbol):
    if get_last_timestamp(symbol) == 0:
        set_last_timestamp(df['timestamp'].iloc[-1], symbol)

    if df['timestamp'].iloc[-1] != get_last_timestamp(symbol):
        await write_live_conditions(df['timestamp'].iloc[-1], symbol)
        set_last_timestamp(df['timestamp'].iloc[-1], symbol)

async def send_data_to_influxdb(symbol, price, timestamp, position_side, position_size, pnl, strategy):
    # Initialize logger inside the function
    logger = get_logger()
    
    try:
        # Rest of the function code...
        pass
    except Exception as e:
        logger.error(f"Error in sending data to influxdb: {e}")