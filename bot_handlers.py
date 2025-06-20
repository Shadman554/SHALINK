"""
Telegram bot handlers for video downloading functionality.
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from video_downloader import VideoDownloader
from config import MESSAGES
import re

logger = logging.getLogger(__name__)

# Initialize video downloader
downloader = VideoDownloader()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    try:
        await update.message.reply_text(MESSAGES["start"])
        logger.info(f"Start command sent to user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video links sent by users."""
    try:
        if not update.message or not update.message.text:
            logger.error("No message or text in update")
            return
            
        user_message = update.message.text.strip()
        user_id = update.effective_user.id
        
        logger.info(f"Received message from user {user_id}: {user_message}")
        logger.info(f"Update object: {update}")
        logger.info(f"Context: {context}")
        
        # Check if message contains a URL
        if not _is_valid_url(user_message):
            await update.message.reply_text(MESSAGES["error_invalid_link"])
            return
        
        # Check if URL is from supported platform
        if not downloader.is_supported_platform(user_message):
            await update.message.reply_text(MESSAGES["error_unsupported"])
            return
        
        # Send processing message
        processing_message = await update.message.reply_text(MESSAGES["processing"])
        
        # Download the video
        file_path, result = downloader.download_video(user_message)
        
        if file_path:
            try:
                # Send the video file
                with open(file_path, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=MESSAGES["completed"],
                        supports_streaming=True
                    )
                
                logger.info(f"Video sent successfully to user {user_id}")
                
            except TelegramError as e:
                if "file is too big" in str(e).lower():
                    await update.message.reply_text("ڤیدیۆکە زۆر گەورەیە، ناتوانرێت بنێردرێت")
                else:
                    await update.message.reply_text(MESSAGES["error_download_failed"])
                logger.error(f"Telegram error sending video: {e}")
            
            except Exception as e:
                await update.message.reply_text(MESSAGES["error_download_failed"])
                logger.error(f"Error sending video: {e}")
            
            finally:
                # Clean up the downloaded file
                downloader.cleanup_file(file_path)
        
        else:
            # Handle different error types
            if result == "unsupported_platform":
                await update.message.reply_text(MESSAGES["error_unsupported"])
            elif result == "file_too_large":
                await update.message.reply_text(MESSAGES["error_file_too_large"])
            elif result == "instagram_auth_required":
                await update.message.reply_text(MESSAGES["error_instagram_auth_required"])
            elif result == "extract_failed" and "instagram.com" in user_message.lower():
                await update.message.reply_text(MESSAGES["error_instagram_auth"])
            else:
                await update.message.reply_text(MESSAGES["error_download_failed"])
            
            logger.error(f"Download failed for user {user_id}: {result}")
        
        # Delete the processing message
        try:
            await processing_message.delete()
        except:
            pass  # Ignore if message is already deleted
            
    except Exception as e:
        logger.error(f"Unexpected error in handle_video_link: {e}")
        try:
            await update.message.reply_text(MESSAGES["error_download_failed"])
        except:
            pass

def _is_valid_url(text: str) -> bool:
    """Check if the text contains a valid URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(text) is not None
