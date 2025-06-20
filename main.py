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
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN

# Configure logging before importing modules that may log during import
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def ensure_single_instance():
    """Prevent multiple bot instances from running."""
    lockfile = os.path.join(tempfile.gettempdir(), 'mediabot.lock')
    try:
        # Windows-specific file locking
        if os.name == 'nt':
            import msvcrt
            fd = os.open(lockfile, os.O_CREAT | os.O_RDWR)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return True
            except IOError:
                return False
        else:
            import fcntl
            fd = os.open(lockfile, os.O_CREAT | os.O_RDWR)
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
    except (IOError, OSError):
        return False

if not ensure_single_instance():
    print("Another bot instance is already running. Exiting.")
    sys.exit(1)

from bot_handlers import start_command, handle_video_link

def main():
    """Main function to run the Telegram bot.
    Keeps retrying if another instance of the bot is already polling.
    """
    while True:
        try:
            # Build a fresh application for every (re)try so internal state is clean
            application = Application.builder().token(BOT_TOKEN).build()

            # Add handlers once per application instance
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))

            logger.info("Bot starting… (polling mode)")

            # Blocking call – returns when the event loop stops
            application.run_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
                timeout=30,
                read_timeout=20,
                write_timeout=20,
                connect_timeout=20,
            )

            # Normal shutdown (e.g., SIGTERM); exit the loop
            logger.info("Bot shut down gracefully – exiting main loop")
            break

        except Conflict as e:
            # Another instance is polling. Wait a bit and try again.
            logger.warning("Telegram conflict detected: %s. Retrying in 5 seconds…", e)
            time.sleep(5)
            continue
        except Exception as e:
            # Log unexpected errors and retry after a short back-off
            logger.error("Unhandled error in polling loop: %s. Retrying in 10 seconds…", e)
            time.sleep(10)
            continue

if __name__ == '__main__':
    main()
