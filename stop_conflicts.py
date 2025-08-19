#!/usr/bin/env python3
"""
Stop bot conflicts by properly handling multiple instances
"""
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError, Conflict

async def stop_bot_conflicts():
    """Stop any existing bot instances using webhooks"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ No bot token found")
        return False
    
    try:
        bot = Bot(token=token)
        
        # Delete any existing webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted and pending updates cleared")
        
        # Get bot info to verify token
        me = await bot.get_me()
        print(f"✅ Bot verified: @{me.username}")
        
        return True
        
    except Conflict as e:
        print(f"⚠️  Conflict detected: {e}")
        return False
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🛑 Stopping bot conflicts...")
    result = asyncio.run(stop_bot_conflicts())
    if result:
        print("✅ Ready for single bot instance")
    else:
        print("❌ Could not resolve conflicts")