from influxdb import InfluxDBClient
from utils.logging import error_logger_func
from utils.globals import set_last_timestamp, get_last_timestamp

logger = error_logger_func()

# InfluxDB istemcisi oluştur
client = InfluxDBClient(host="localhost", port=8086, database="n0name-db")


# Gerçek zamanlı veri yazma fonksiyonu
async def write_live_data(last_candle, symbol):


    try:
        timestamp = last_candle['timestamp']
        open_price = last_candle['open']
        high_price = last_candle['high']
        low_price = last_candle['low']
        close_price = last_candle['close']
        volume = last_candle['volume']

        # InfluxDB’ye veri yaz
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
        client = InfluxDBClient(host="localhost", port=8086, database="n0name-db")
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