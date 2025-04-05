import csv
from datetime import datetime
from utils.globals import get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc
import os
import sys


def write_to_daily_csv(symbol):

    buycond1 = get_buyconda(symbol)
    buycond2 = get_buycondb(symbol)
    buycond3 = get_buycondc(symbol)
    sellcond1 = get_sellconda(symbol)
    sellcond2 = get_sellcondb(symbol)
    sellcond3 = get_sellcondc(symbol)

    current_date = datetime.now().strftime("%Y-%m-%d")

    if getattr(sys, 'frozen', False):
        BASE_PATH = os.path.dirname(sys.executable)
    else:
        # Running as Python script
        BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        BASE_PATH = os.path.dirname(BASE_PATH)
        BASE_PATH = os.path.dirname(BASE_PATH)

    archive_dir = os.path.join(BASE_PATH, "condition_archive")
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    filename = os.path.join(BASE_PATH, f"{symbol}_{current_date}.csv")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    row = [timestamp, symbol, buycond1, buycond2, buycond3, sellcond1, sellcond2, sellcond3]
    

    try:
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["timestamp", "symbol", "buycond1", "buycond2", "buycond3", 
                                 "sellcond1", "sellcond2", "sellcond3"])
            
            writer.writerow(row)
    
    except Exception as e:
        print(f"CSV yazma hatası: {e}")