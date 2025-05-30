from utils.globals import get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc, get_funding_flag
from colorama import init, Fore, Style
from utils.cursor_movement import logger_move_cursor_up, clean_line
import asyncio
from utils.enhanced_logging import get_logger

async def current_status(symbols, client):
    # Initialize logger inside the function
    logger = get_logger(__name__)
    
    try:    
        status_lines_count = 0
        buy_status = ""
        sell_status = ""
        current_status = {}
        for symbol in symbols:
            # Alım koşulları
            buyCondA = get_buyconda(symbol)
            buyCondB = get_buycondb(symbol)
            buyCondC = get_buycondc(symbol)
            funding_period = get_funding_flag(symbol)


            # Satım koşulları (örnek olarak tanımlandı, kendi kodunuza göre uyarlayın)
            sellCondA = get_sellconda(symbol)
            sellCondB = get_sellcondb(symbol)
            sellCondC = get_sellcondc(symbol)

            # Alım durumu satırı
            buy_status = (
                f"{Style.BRIGHT}{symbol}{Style.RESET_ALL}    -   Funding Period : {Fore.GREEN if funding_period else Fore.RED}{funding_period}{Style.RESET_ALL}"
                f"\n\nBuyCondition1 : {Fore.GREEN if buyCondA else Fore.RED}{buyCondA}{Style.RESET_ALL},     "
                f"BuyCondition2 : {Fore.GREEN if buyCondB else Fore.RED}{buyCondB}{Style.RESET_ALL},    "
                f"BuyCondition3 : {Fore.GREEN if buyCondC else Fore.RED}{buyCondC}{Style.RESET_ALL}     "
            )

            # Satım durumu satırı
            sell_status = (
                f"SellCondition1: {Fore.GREEN if sellCondA else Fore.RED}{sellCondA}{Style.RESET_ALL},     "
                f"SellCondition2: {Fore.GREEN if sellCondB else Fore.RED}{sellCondB}{Style.RESET_ALL},    "
                f"SellCondition3: {Fore.GREEN if sellCondC else Fore.RED}{sellCondC}{Style.RESET_ALL}  "
                f"\n"
            )

            current_status[symbol] = buy_status + "\n" + sell_status
            
        status_lines_count = (len(symbols) * 5) 

        all_status = current_status.values()
        all_status = "\n".join(all_status)

        logger_move_cursor_up(status_lines_count)
        for _ in range(status_lines_count):
            print("                                                                                                                                                                     ")
        logger_move_cursor_up(status_lines_count)
        print(all_status)

    except Exception as e:
        logger.error(f"Current status error: {e}")

async def current_position_monitor(p, pricePrecisions, logger):
    try:
        if float(p['positionAmt']) > 0:
            long_status = (f"{Style.BRIGHT}{p['symbol']}: {Fore.GREEN}LONG{Style.RESET_ALL}   {Style.BRIGHT}Size: {Fore.BLUE}${abs(round(float(p['notional']),2))}{Style.RESET_ALL},    {Style.BRIGHT}P&L: {Fore.GREEN if float(p['unRealizedProfit']) > 0 else Fore.RED}${float(p['unRealizedProfit']):.2f}{Style.RESET_ALL},    {Style.BRIGHT}Entry Price: {Fore.LIGHTCYAN_EX}${round(float(p['entryPrice']), pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}Current Price: {Fore.MAGENTA}${round(float(p['markPrice']), pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}TP: {Fore.LIGHTGREEN_EX}${round(float(p['entryPrice']) * 1.0033, pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}SL: {Fore.LIGHTRED_EX}${round(float(p['entryPrice']) * 0.993 , pricePrecisions[p['symbol']])}{Style.RESET_ALL}")
            return long_status
        if float(p['positionAmt']) < 0:
            short_status = (f"{Style.BRIGHT}{p['symbol']}: {Fore.RED}SHORT{Style.RESET_ALL}   {Style.BRIGHT}Size: {Fore.BLUE}${abs(round(float(p['notional']),2))}{Style.RESET_ALL},    {Style.BRIGHT}P&L: {Fore.GREEN if float(p['unRealizedProfit']) > 0 else Fore.RED}${float(p['unRealizedProfit']):.2f}{Style.RESET_ALL},    {Style.BRIGHT}Entry Price: {Fore.LIGHTCYAN_EX}${round(float(p['entryPrice']), pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}Current Price: {Fore.MAGENTA}${round(float(p['markPrice']), pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}TP: {Fore.LIGHTGREEN_EX}${round(float(p['entryPrice']) * 0.9966, pricePrecisions[p['symbol']])}{Style.RESET_ALL},    {Style.BRIGHT}SL: {Fore.LIGHTRED_EX}${round(float(p['entryPrice']) * 1.007 , pricePrecisions[p['symbol']])}{Style.RESET_ALL}")
            return short_status

    except Exception as e:
        logger.error(f"Position monitoring error: {e}")
        await asyncio.sleep(2)

def status_printer(status, position_response):
    if status:
        clean_line(3)
        print("Open Positions: \n" + position_response)
        logger_move_cursor_up(2)
    else:
        clean_line(3)
        print("No Open Positions !")
        logger_move_cursor_up(1)