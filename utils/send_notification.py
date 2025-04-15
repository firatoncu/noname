from telegram import Bot
from utils.load_config import load_config

async def send_position_close_alert(tp, symbol, side, profit):
    
    config = load_config()
    TOKEN = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    username = config['username']
    
    bot = Bot(token=TOKEN)
    # Replace 'CHAT_ID' with the chat ID you want to send to
    # You can get chat ID by messaging @getidsbot

    if side == "LONG":
        s = "🔼"
    else:
        s = "🔽"
    
    # Enhanced HTML-formatted message
    if tp:
        message = (
        "🚀 <b>Take Profit Order Completed!</b> 💎\n"
        "✦──────✦─────✦\n"  # Unicode line for separation
        f"🌐 <b>Symbol : {symbol}</b>\n\n"
        f"{s} <b>Side   : {side}</b>\n\n"
        f"💰 <b>Profit : ${profit}</b> 📈\n\n"
        f"🗣️ <b>User   : {username}</b> "
        )
    else:
        message = (
        "💥 <b>Stop Loss Order Executed!</b> 🔔\n"
        "✦──────✦─────✦\n"  # Same fancy separator
        f"🌐 <b>Symbol : {symbol}</b>\n\n"
        f"{s} <b>Side   : {side}</b>\n\n"
        f"💸 <b>Loss   : ${profit}</b> 📉\n\n"
        f"🗣️ <b>User   : {username}</b> "
        )
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=4,
            text=message,
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Error: {e}")



async def send_position_open_alert(symbol):
    
    config = load_config()
    TOKEN = config['telegram']['token']
    chat_id = config['telegram']['chat_id']
    username = config['username']
    
    bot = Bot(token=TOKEN)
    # Replace 'CHAT_ID' with the chat ID you want to send to
    # You can get chat ID by messaging @getidsbo
    
    # Enhanced HTML-formatted message
    
    message = (
        "🌀 <b>Position Opened</b> 💠\n"
        "✦──────✦─────✦\n"  # Unicode line for separation
        f"🌐 <b>Symbol : {symbol}</b>"
        )

    
    try:
        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=4,
            text=message,
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Error: {e}")