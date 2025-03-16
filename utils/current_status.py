from utils.globals import get_buyconda, get_buycondb, get_buycondc, get_sellconda, get_sellcondb, get_sellcondc 
from colorama import init, Fore, Style
import sys
from utils.cursor_movement import move_cursor_up, save_cursor_position, restore_cursor_position

init()

async def current_status(symbols):       
    status_lines_count = 0
    buy_status = ""
    sell_status = ""
    current_status = {}
    for symbol in symbols:
        # Alım koşulları
        buyCondA = get_buyconda(symbol)
        buyCondB = get_buycondb(symbol)
        buyCondC = get_buycondc(symbol)

        # Satım koşulları (örnek olarak tanımlandı, kendi kodunuza göre uyarlayın)
        sellCondA = get_sellconda(symbol)
        sellCondB = get_sellcondb(symbol)
        sellCondC = get_sellcondc(symbol)

        # Alım durumu satırı
        buy_status = (
            f"{Style.BRIGHT}{symbol}{Style.RESET_ALL}"
            f"\nBuyCondition1 : {Fore.GREEN if buyCondA else Fore.RED}{buyCondA}{Style.RESET_ALL},     "
            f"BuyCondition2 : {Fore.GREEN if buyCondB else Fore.RED}{buyCondB}{Style.RESET_ALL},    "
            f"BuyCondition3 : {Fore.GREEN if buyCondC else Fore.RED}{buyCondC}{Style.RESET_ALL}       "
        )

        # Satım durumu satırı
        sell_status = (
            f"\nSellCondition1: {Fore.GREEN if sellCondA else Fore.RED}{sellCondA}{Style.RESET_ALL},     "
            f"SellCondition2: {Fore.GREEN if sellCondB else Fore.RED}{sellCondB}{Style.RESET_ALL},    "
            f"SellCondition3: {Fore.GREEN if sellCondC else Fore.RED}{sellCondC}{Style.RESET_ALL}   "
            f"\n"
        )

        current_status[symbol] = buy_status + "\n" + sell_status
        
    status_lines_count = (len(symbols) * 5) 

    all_status = current_status.values()
    all_status = "\n".join(all_status)


    move_cursor_up(status_lines_count)
    save_cursor_position()
    restore_cursor_position()
        # Terminali güncelle
    for _ in range(status_lines_count):
        print(" ")
    move_cursor_up(status_lines_count)
    save_cursor_position()
    restore_cursor_position()
    # Durum satırlarını yaz
    print(all_status)