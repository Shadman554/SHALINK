#!/usr/bin/env python3
"""
Telegram Bot for downloading videos from TikTok, Instagram, and Facebook
with Kurdish language responses.
"""

import os
import sys
import tempfile
import logging
import time
from telegram.error import Conflict
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN

# Configure logging before importing modules that may log during import
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def force_cleanup_bot_instance():
    """Force cleanup any existing bot instances."""
    lockfile = os.path.join(tempfile.gettempdir(), 'mediabot.lock')
    try:
        if os.path.exists(lockfile):
            os.remove(lockfile)
            logger.info("Removed existing bot lock file")
    except Exception as e:
        logger.warning(f"Could not remove lock file: {e}")

# Force cleanup any existing instances
force_cleanup_bot_instance()

from bot_handlers import start_command, handle_video_link, handle_youtube_callback

def main():
    """Main function to run the Telegram bot.
    Aggressively takes over the bot token from any other instances.
    """
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        try:
            attempt += 1
            logger.info(f"Bot startup attempt {attempt}/{max_attempts}")
            
            # Build application with aggressive settings to take over
            application = Application.builder().token(BOT_TOKEN).build()

            # Add handlers once per application instance
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))
            application.add_handler(CallbackQueryHandler(handle_youtube_callback, pattern=r"^yt_(video|audio)_"))

            logger.info("Bot starting… (polling mode)")

            # Blocking call with aggressive takeover settings
            logger.info("Bot starting with aggressive conflict resolution")
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
                close_loop=False
            )

            # Normal shutdown (e.g., SIGTERM); exit the loop
            logger.info("Bot shut down gracefully – exiting main loop")
            break

        except Conflict as e:
            # Another instance is polling. Force take over with minimal delay
            logger.warning("Conflict detected. Attempting immediate takeover (attempt %d/%d)", attempt, max_attempts)
            if attempt >= max_attempts:
                logger.error("Max attempts reached. Bot will force-start anyway.")
                # Try one more time with most aggressive settings
                try:
                    application = Application.builder().token(BOT_TOKEN).build()
                    logger.info("Final attempt - Bot starting with force override")
                    application.run_polling(
                        allowed_updates=["message"],
                        drop_pending_updates=True,
                        close_loop=False
                    )
                    break
                except Exception as final_error:
                    logger.error(f"Final attempt failed: {final_error}")
                    break
            time.sleep(0.5)  # Very short delay
            continue
        except Exception as e:
            # Log unexpected errors and retry after a short back-off
            logger.error("Unhandled error in polling loop: %s. Retrying in 10 seconds…", e)
            time.sleep(10)
            continue

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
        print("Please set your Telegram Bot Token before running the bot.")
        sys.exit(1)
    main()
