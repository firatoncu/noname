from utils.globals import set_db_status, set_notif_status
from utils.influxdb.inf_db_initializer import inf_db_init_main

async def db_status_check():
    db_status = (input("Do you want to use the InfluxDB? (y/n): ").strip().lower() or "n")
    
    if db_status == "y":
        set_db_status(True)
        inf_db_init_main()
    else:
        set_db_status(False)