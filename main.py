#!/usr/bin/env python3
"""
Telegram Bot for downloading videos from TikTok, Instagram, Facebook, YouTube,
Twitter/X, and Pinterest — with Kurdish language responses.
"""

import os
import sys
import datetime
import tempfile
import logging
import time
from telegram.error import Conflict, NetworkError, TimedOut
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from config import BOT_TOKEN, BOT_MAX_CONCURRENT_DOWNLOADS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def force_cleanup_bot_instance():
    lockfile = os.path.join(tempfile.gettempdir(), 'mediabot.lock')
    try:
        if os.path.exists(lockfile):
            os.remove(lockfile)
            logger.info("Removed existing bot lock file")
    except Exception as e:
        logger.warning(f"Could not remove lock file: {e}")


force_cleanup_bot_instance()

from bot_handlers import (
    start_command, handle_video_link,
    handle_youtube_callback, handle_download_callback,
    admin_command, broadcast_command,
    user_command, ban_command, unban_command,
    send_daily_report
)


async def error_handler(update, context):
    err = context.error
    if isinstance(err, (Conflict, NetworkError, TimedOut)):
        logger.warning("Transient error (ignored): %s", err)
    else:
        logger.error("Unhandled update error: %s", err, exc_info=err)


def main():
    attempt = 0

    while True:
        try:
            attempt += 1
            logger.info(f"Bot startup attempt {attempt}")

            application = (
                Application.builder()
                .token(BOT_TOKEN)
                .read_timeout(60)
                .write_timeout(300)
                .connect_timeout(30)
                .pool_timeout(60)
                .connection_pool_size(max(8, BOT_MAX_CONCURRENT_DOWNLOADS * 4))
                .concurrent_updates(max(4, BOT_MAX_CONCURRENT_DOWNLOADS * 2))
                .build()
            )

            # User commands
            application.add_handler(CommandHandler("start", start_command))

            # Admin commands
            application.add_handler(CommandHandler("admin", admin_command))
            application.add_handler(CommandHandler("broadcast", broadcast_command))
            application.add_handler(CommandHandler("user", user_command))
            application.add_handler(CommandHandler("ban", ban_command))
            application.add_handler(CommandHandler("unban", unban_command))

            # Message handler
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))

            # Callback handlers
            application.add_handler(CallbackQueryHandler(
                handle_youtube_callback, pattern=r"^yt_(video_(360|720|1080)|audio)_"
            ))
            application.add_handler(CallbackQueryHandler(
                handle_download_callback, pattern=r"^dl_(video|audio)_"
            ))

            application.add_error_handler(error_handler)

            # Daily report job at 09:00 UTC
            if application.job_queue:
                application.job_queue.run_daily(
                    send_daily_report,
                    time=datetime.time(9, 0, 0, tzinfo=datetime.timezone.utc),
                    name="daily_report"
                )
                logger.info("Daily report job scheduled at 09:00 UTC")
            else:
                logger.warning("JobQueue not available — daily report disabled. Install APScheduler.")

            logger.info("Bot starting… (polling mode)")
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
            )

            logger.info("Bot shut down gracefully – exiting main loop")
            break

        except Conflict as e:
            wait_seconds = min(60, 10 + attempt * 5)
            logger.warning(
                "Telegram polling conflict detected. Another instance is using this bot token. "
                "Waiting %s seconds before retrying: %s",
                wait_seconds,
                e,
            )
            time.sleep(wait_seconds)
            continue
        except Exception as e:
            logger.error("Unhandled error in polling loop: %s. Retrying in 10 seconds…", e)
            time.sleep(10)
            continue


if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
        print("Please set your Telegram Bot Token before running the bot.")
        sys.exit(1)
    main()
