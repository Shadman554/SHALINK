#!/usr/bin/env python3
"""
Telegram Bot for downloading videos from TikTok, Instagram, and Facebook
with Kurdish language responses.
"""

import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from bot_handlers import start_command, handle_video_link

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Telegram bot."""
    try:
        # Create the Application with conflict resolution
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
        
        logger.info("Bot started successfully")
        
        # Run the bot with conflict resolution
        application.run_polling(
            allowed_updates=["message"],
            drop_pending_updates=True,
            timeout=30,
            read_timeout=20,
            write_timeout=20,
            connect_timeout=20
        )
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()
