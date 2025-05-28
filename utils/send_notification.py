from telegram import Bot
from utils.load_config import load_config
import asyncio
from datetime import datetime
import traceback

async def send_position_close_alert(tp, symbol, side, profit):
    """
    Send a beautifully formatted position close alert via Telegram.
    
    Args:
        tp (bool): True if take profit, False if stop loss
        symbol (str): Trading symbol
        side (str): Position side (LONG/SHORT)
        profit (float): Profit/loss amount
    """
    try:
        config = load_config()
        TOKEN = config['telegram']['token']
        chat_id = config['telegram']['chat_id']
        username = config.get('username', 'Trader')
        
        bot = Bot(token=TOKEN)
        
        # Enhanced emoji and formatting
        if side == "LONG":
            side_emoji = "📈"
            direction_emoji = "🔼"
        else:
            side_emoji = "📉"
            direction_emoji = "🔽"
        
        # Current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced HTML-formatted message with better structure
        if tp:
            # Take Profit message
            message = (
                f"🎯 <b>TAKE PROFIT EXECUTED!</b> 🎯\n"
                f"{'═' * 15}\n\n"
                f"💎 <b>Position Closed Successfully</b>\n\n"
                f"📊 <b>Symbol:</b> <code>{symbol}</code>\n"
                f"{direction_emoji} <b>Side:</b> <code>{side}</code> {side_emoji}\n"
                f"💰 <b>Profit:</b> <code>${profit:.2f}</code> ✅\n"
                f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"
                f"👤 <b>Trader:</b> <code>{username}</code>\n\n"
            )
        else:
            # Stop Loss message
            message = (
                f"🛑 <b>STOP LOSS TRIGGERED!</b> 🛑\n"
                f"{'═' * 15}\n\n"
                f"⚠️ <b>Position Closed for Protection</b>\n\n"
                f"📊 <b>Symbol:</b> <code>{symbol}</code>\n"
                f"{direction_emoji} <b>Side:</b> <code>{side}</code> {side_emoji}\n"
                f"💸 <b>Loss:</b> <code>-${profit:.2f}</code> ❌\n"
                f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"
                f"👤 <b>Trader:</b> <code>{username}</code>\n\n"
            )
        
        # Send message with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=4,
                    text=message,
                    parse_mode='HTML'
                )
                print(f"✅ Position close notification sent successfully for {symbol}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Telegram send attempt {attempt + 1} failed, retrying... Error: {e}")
                    await asyncio.sleep(1)
                else:
                    print(f"❌ Failed to send Telegram notification after {max_retries} attempts: {e}")
                    raise

    except Exception as e:
        print(f"❌ Error in send_position_close_alert: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")


async def send_position_open_alert(symbol, side):
    """
    Send a beautifully formatted position open alert via Telegram.
    
    Args:
        symbol (str): Trading symbol
        side (str): Position side (LONG/SHORT)
    """
    try:
        config = load_config()
        TOKEN = config['telegram']['token']
        chat_id = config['telegram']['chat_id']
        username = config.get('username', 'Trader')
        
        bot = Bot(token=TOKEN)
        
        # Enhanced emoji and formatting
        if side == "LONG":
            side_emoji = "📈"
            direction_emoji = "🔼"
            action_emoji = "🚀"
        else:
            side_emoji = "📉"
            direction_emoji = "🔽"
            action_emoji = "🎯"
        
        # Current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced HTML-formatted message
        message = (
            f"{action_emoji} <b>NEW POSITION OPENED!</b> {action_emoji}\n"
            f"{'═' * 15}\n\n"
            f"🎯 <b>Position Initiated</b>\n\n"
            f"📊 <b>Symbol:</b> <code>{symbol}</code>\n"
            f"{direction_emoji} <b>Side:</b> <code>{side}</code> {side_emoji}\n"
            f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"
            f"👤 <b>Trader:</b> <code>{username}</code>\n\n"
        )
        
        # Send message with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=4,
                    text=message,
                    parse_mode='HTML'
                )
                print(f"✅ Position open notification sent successfully for {symbol}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Telegram send attempt {attempt + 1} failed, retrying... Error: {e}")
                    await asyncio.sleep(1)
                else:
                    print(f"❌ Failed to send Telegram notification after {max_retries} attempts: {e}")
                    raise

    except Exception as e:
        print(f"❌ Error in send_position_open_alert: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")


async def send_tp_limit_filled_alert(symbol, side):
    """
    Send a beautifully formatted limit order filled alert via Telegram.
    
    Args:
        symbol (str): Trading symbol
        side (str): Position side (LONG/SHORT)
    """
    try:
        config = load_config()
        TOKEN = config['telegram']['token']
        chat_id = config['telegram']['chat_id']
        username = config.get('username', 'Trader')
        
        bot = Bot(token=TOKEN)
        
        # Enhanced emoji and formatting
        if side == "LONG":
            direction_emoji = "🔼"
            side_emoji = "📈"
        else:
            direction_emoji = "🔽"
            side_emoji = "📉"
        
        # Current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced HTML-formatted message
        message = (
            f"🎯 <b>LIMIT ORDER FILLED!</b> 🎯\n"
            f"{'═' * 15}\n\n"
            f"✅ <b>Take Profit Order Executed</b>\n\n"
            f"📊 <b>Symbol:</b> <code>{symbol}</code>\n"
            f"{direction_emoji} <b>Side:</b> <code>{side}</code> {side_emoji}\n"
            f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"
            f"👤 <b>Trader:</b> <code>{username}</code>\n\n"
            f"🎉 <i>Limit order successfully executed!</i> 🎉"
        )
        
        # Send message with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=4,
                    text=message,
                    parse_mode='HTML'
                )
                print(f"✅ Limit order notification sent successfully for {symbol}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Telegram send attempt {attempt + 1} failed, retrying... Error: {e}")
                    await asyncio.sleep(1)
                else:
                    print(f"❌ Failed to send Telegram notification after {max_retries} attempts: {e}")
                    raise

    except Exception as e:
        print(f"❌ Error in send_tp_limit_filled_alert: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")


# Test function to verify notifications are working
async def test_notifications():
    """Test function to verify all notification types are working."""
    print("🧪 Testing notification system...")
    
    try:
        # Test position open
        await send_position_open_alert("BTCUSDT", "LONG")
        await asyncio.sleep(2)
        
        # Test position close (profit)
        await send_position_close_alert(True, "BTCUSDT", "LONG", 15.50)
        await asyncio.sleep(2)
        
        # Test position close (loss)
        await send_position_close_alert(False, "ETHUSDT", "SHORT", 8.25)
        await asyncio.sleep(2)
        
        # Test limit order filled
        await send_tp_limit_filled_alert("SOLUSDT", "LONG")
        
        print("✅ All notification tests completed!")
        
    except Exception as e:
        print(f"❌ Notification test failed: {e}")


if __name__ == "__main__":
    # Run test if script is executed directly
    asyncio.run(test_notifications())