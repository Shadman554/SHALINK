"""
Telegram bot handlers for video downloading functionality.
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from video_downloader import VideoDownloader
from config import MESSAGES
import re
from urllib.parse import urlparse

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

def _is_youtube_url(url: str) -> bool:
    """Check if URL is from YouTube."""
    try:
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain in ['youtube.com', 'youtu.be', 'm.youtube.com']
    except Exception:
        return False

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
        
        # Special handling for YouTube URLs - show format options
        if _is_youtube_url(user_message):
            keyboard = [
                [InlineKeyboardButton(MESSAGES["youtube_video_1080"], callback_data=f"yt_video_{user_id}")],
                [InlineKeyboardButton(MESSAGES["youtube_audio_mp3"], callback_data=f"yt_audio_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Store the URL in context for later use
            context.user_data[f'youtube_url_{user_id}'] = user_message
            
            await update.message.reply_text(MESSAGES["youtube_options"], reply_markup=reply_markup)
            return
        
        # For non-YouTube platforms, proceed with normal download
        processing_message = await update.message.reply_text(MESSAGES["processing"])
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
                    # Try to compress the video
                    compress_msg = await update.message.reply_text(MESSAGES["compressing"])
                    compressed_path = downloader.compress_video(file_path)
                    
                    if compressed_path:
                        try:
                            with open(compressed_path, 'rb') as compressed_file:
                                await update.message.reply_video(
                                    video=compressed_file,
                                    caption=MESSAGES["completed"],
                                    supports_streaming=True
                                )
                            logger.info(f"Compressed video sent successfully to user {user_id}")
                            # Clean up compressed file
                            downloader.cleanup_file(compressed_path)
                        except Exception as comp_e:
                            await update.message.reply_text(MESSAGES["error_download_failed"])
                            logger.error(f"Error sending compressed video: {comp_e}")
                    else:
                        await update.message.reply_text(MESSAGES["error_file_too_large"])
                    
                    try:
                        await compress_msg.delete()
                    except:
                        pass
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

async def handle_youtube_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube format selection callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        callback_data = query.data
        user_id = update.effective_user.id
        
        # Get the stored YouTube URL
        youtube_url = context.user_data.get(f'youtube_url_{user_id}')
        if not youtube_url:
            await query.edit_message_text("خەپە! ناتوانم URL بدۆزمەوە، تکایە دووبارە تاقی بکەوە")
            return
        
        # Determine format based on callback
        if callback_data.startswith('yt_video_'):
            format_type = 'video'
            processing_msg = MESSAGES["processing_video"]
            completed_msg = MESSAGES["completed_video"]
        elif callback_data.startswith('yt_audio_'):
            format_type = 'audio'
            processing_msg = MESSAGES["processing_audio"]
            completed_msg = MESSAGES["completed_audio"]
        else:
            await query.edit_message_text(MESSAGES["error_download_failed"])
            return
        
        # Update message to show processing
        await query.edit_message_text(processing_msg)
        
        # Download with specified format
        file_path, result = downloader.download_youtube(youtube_url, format_type)
        
        if file_path:
            try:
                # Send the file
                if format_type == 'audio':
                    with open(file_path, 'rb') as audio_file:
                        await context.bot.send_audio(
                            chat_id=query.message.chat_id,
                            audio=audio_file,
                            caption=completed_msg
                        )
                else:
                    with open(file_path, 'rb') as video_file:
                        await context.bot.send_video(
                            chat_id=query.message.chat_id,
                            video=video_file,
                            caption=completed_msg,
                            supports_streaming=True
                        )
                
                logger.info(f"YouTube {format_type} sent successfully to user {user_id}")
                
            except TelegramError as e:
                if "file is too big" in str(e).lower():
                    # Try to compress the video/audio
                    await context.bot.send_message(query.message.chat_id, MESSAGES["compressing"])
                    compressed_path = downloader.compress_video(file_path)
                    
                    if compressed_path:
                        try:
                            if format_type == 'audio':
                                with open(compressed_path, 'rb') as compressed_file:
                                    await context.bot.send_audio(
                                        chat_id=query.message.chat_id,
                                        audio=compressed_file,
                                        caption=completed_msg
                                    )
                            else:
                                with open(compressed_path, 'rb') as compressed_file:
                                    await context.bot.send_video(
                                        chat_id=query.message.chat_id,
                                        video=compressed_file,
                                        caption=completed_msg,
                                        supports_streaming=True
                                    )
                            logger.info(f"Compressed YouTube {format_type} sent successfully to user {user_id}")
                            # Clean up compressed file
                            downloader.cleanup_file(compressed_path)
                        except Exception as comp_e:
                            await context.bot.send_message(query.message.chat_id, MESSAGES["error_download_failed"])
                            logger.error(f"Error sending compressed YouTube {format_type}: {comp_e}")
                    else:
                        await context.bot.send_message(query.message.chat_id, MESSAGES["error_file_too_large"])
                else:
                    await context.bot.send_message(query.message.chat_id, MESSAGES["error_download_failed"])
                logger.error(f"Telegram error sending YouTube {format_type}: {e}")
            
            except Exception as e:
                await context.bot.send_message(query.message.chat_id, MESSAGES["error_download_failed"])
                logger.error(f"Error sending YouTube {format_type}: {e}")
            
            finally:
                # Clean up the downloaded file
                downloader.cleanup_file(file_path)
                # Delete the options message
                try:
                    await query.delete_message()
                except:
                    pass
        else:
            await query.edit_message_text(MESSAGES["error_download_failed"])
            logger.error(f"YouTube {format_type} download failed for user {user_id}: {result}")
        
        # Clean up stored URL
        context.user_data.pop(f'youtube_url_{user_id}', None)
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_youtube_callback: {e}")
        try:
            await query.edit_message_text(MESSAGES["error_download_failed"])
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
