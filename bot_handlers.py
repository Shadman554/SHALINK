"""
Telegram bot handlers for video downloading functionality.
"""

import os
import re
import time
import asyncio
import logging
import datetime
import uuid
from urllib.parse import urlparse

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.error import TelegramError, TimedOut, NetworkError

from video_downloader import VideoDownloader
from database import (
    register_user, record_download, get_all_user_ids, get_all_users,
    get_global_stats,
    ban_user, unban_user, is_banned, get_user_info, get_user_info_by_username,
    get_daily_stats, get_download_history, init_db
)
from config import (
    MESSAGES, ADMIN_USER_ID, SUPPORTED_PLATFORMS,
    BOT_MAX_CONCURRENT_DOWNLOADS, BOT_MAX_BATCH_LINKS
)

logger = logging.getLogger(__name__)

downloader = VideoDownloader()
init_db()
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(BOT_MAX_CONCURRENT_DOWNLOADS)

URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_urls(text: str) -> list[str]:
    return URL_PATTERN.findall(text)


def _is_youtube_url(url: str) -> bool:
    try:
        domain = urlparse(url.lower()).netloc.lstrip('www.')
        return domain in ('youtube.com', 'youtu.be', 'm.youtube.com')
    except Exception:
        return False


def _is_supported(url: str) -> bool:
    try:
        domain = urlparse(url.lower()).netloc.lstrip('www.')
        return any(p in domain for p in SUPPORTED_PLATFORMS)
    except Exception:
        return False


def _detect_platform(url: str) -> str:
    url_lower = url.lower()
    if 'tiktok' in url_lower:
        return 'TikTok'
    if 'instagram' in url_lower:
        return 'Instagram'
    if 'facebook' in url_lower or 'fb.com' in url_lower:
        return 'Facebook'
    if 'youtube' in url_lower or 'youtu.be' in url_lower:
        return 'YouTube'
    if 'twitter' in url_lower or 'x.com' in url_lower or 't.co' in url_lower:
        return 'Twitter/X'
    if 'pinterest' in url_lower or 'pin.it' in url_lower:
        return 'Pinterest'
    return 'Video'


def _is_admin(user_id: int) -> bool:
    admin_id = _get_admin_id()
    return admin_id != 0 and user_id == admin_id


def _get_admin_id() -> int:
    try:
        return int(os.getenv("ADMIN_USER_ID", "0"))
    except (TypeError, ValueError):
        return 0


async def _check_banned(update: Update) -> bool:
    """Returns True (and replies) if the user is banned. Caller should return immediately."""
    if is_banned(update.effective_user.id):
        await update.message.reply_text(
            MESSAGES["banned_message"],
            disable_web_page_preview=True
        )
        return True
    return False


def _make_progress_hook(loop, message):
    """Return (hook, stop_fn). Call stop_fn() before deleting the message."""
    last_pct = [-1]
    last_edit_time = [0.0]
    stopped = [False]
    MIN_INTERVAL = 3.0  # seconds between Telegram edits

    def hook(d):
        if stopped[0]:
            return
        if d.get('status') != 'downloading':
            return
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if not total or total <= 0:
            return
        pct = int(downloaded / total * 100)
        rounded = (pct // 5) * 5
        now = time.monotonic()
        if rounded != last_pct[0] and (now - last_edit_time[0]) >= MIN_INTERVAL:
            last_pct[0] = rounded
            last_edit_time[0] = now
            asyncio.run_coroutine_threadsafe(
                message.edit_text(
                    MESSAGES["downloading"].format(rounded),
                    disable_web_page_preview=True
                ),
                loop
            )

    def stop():
        stopped[0] = True

    return hook, stop


async def _send_video_file(context, chat_id, file_path, caption):
    with open(file_path, 'rb') as f:
        await context.bot.send_video(
            chat_id=chat_id, video=f, caption=caption, supports_streaming=True
        )


async def _send_audio_file(context, chat_id, file_path, caption):
    with open(file_path, 'rb') as f:
        await context.bot.send_audio(chat_id=chat_id, audio=f, caption=caption)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        # Register the user without incrementing the download counter
        register_user(user.id, user.username or '', user.first_name or '')
        await update.message.reply_text(
            MESSAGES["start"], disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not _is_admin(update.effective_user.id):
            await update.message.reply_text(MESSAGES["broadcast_no_access"])
            return

        total_users, total_downloads = get_global_stats()
        all_users = get_all_users()

        text = (
            "🔐 فەرمانەکانی ئەدمین:\n\n"
            "/admin — ئامار و لیستی بەکارهێنەران\n"
            "/broadcast <پەیام> — ناردنی پەیام بۆ هەموو بەکارهێنەران\n"
            "/user <id یان @username> — زانیاری بەکارهێنەر\n"
            "/ban <id> — بانکردنی بەکارهێنەر\n"
            "/unban <id> — لابردنی بانی بەکارهێنەر\n\n"
            "━━━━━━━━━━━━━━━\n"
            "📊 ئامارەکانی بۆت:\n\n"
            f"👥 کۆی بەکارهێنەران: {total_users}\n"
            f"⬇️ کۆی دابەزاندنەکان: {total_downloads}\n\n"
            "━━━━━━━━━━━━━━━\n"
            "👤 لیستی بەکارهێنەران:\n\n"
        )

        if not all_users:
            text += "هیچ بەکارهێنەرێک نییە."
        else:
            for uid, first_name, username, dl_count, last_used in all_users:
                name = first_name or '-'
                uname = f"@{username}" if username else '-'
                date = str(last_used)[:10] if last_used else '-'
                text += f"• {name} ({uname})\n  ID: {uid} | دابەزاندن: {dl_count} | دوایین: {date}\n\n"

        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await update.message.reply_text(text[i:i+4000])
        else:
            await update.message.reply_text(text)

    except Exception as e:
        logger.error(f"Error in admin_command: {e}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        admin_id = _get_admin_id()
        logger.info(f"Broadcast check — user_id={user_id}, admin_id={admin_id}")
        if admin_id == 0 or user_id != admin_id:
            await update.message.reply_text(MESSAGES["broadcast_no_access"])
            return
        raw = update.message.text or ""
        message_text = raw.split(None, 1)[1].strip() if " " in raw or "\n" in raw else ""
        if not message_text:
            await update.message.reply_text(MESSAGES["broadcast_usage"])
            return
        user_ids = get_all_user_ids()
        sent = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=message_text)
                sent += 1
                await asyncio.sleep(0.05)  # Stay within Telegram's 30 msg/s flood limit
            except Exception:
                pass
        await update.message.reply_text(MESSAGES["broadcast_done"].format(sent))
    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")


async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not _is_admin(update.effective_user.id):
            await update.message.reply_text(MESSAGES["broadcast_no_access"])
            return
        raw = (update.message.text or "").strip()
        parts = raw.split(None, 1)
        arg = (context.args[0] if context.args else (parts[1].strip() if len(parts) > 1 else "")).strip()
        if not arg:
            await update.message.reply_text(MESSAGES["user_usage"])
            return
        logger.info(f"user_command lookup arg='{arg}'")
        try:
            row = get_user_info(int(arg))
        except ValueError:
            row = get_user_info_by_username(arg)
        if not row:
            await update.message.reply_text(MESSAGES["user_not_found"])
            return
        uid, username, first_name, dl_count, first_used, last_used = row
        banned = "✅ بانکراو" if is_banned(uid) else "🟢 ئازاد"

        text = (
            f"👤 زانیاری بەکارهێنەر:\n"
            f"• ID: {uid}\n"
            f"• ناو: {first_name or '-'}\n"
            f"• بەکارهێنەر: @{username or '-'}\n"
            f"• دۆخ: {banned}\n"
            f"• کۆی دابەزاندن: {dl_count} جار\n"
            f"• یەکەم جار: {str(first_used or '')[:16]}\n"
            f"• دوایین جار: {str(last_used or '')[:16]}\n"
        )

        # Download history
        history = get_download_history(uid, limit=50)
        text += f"\n━━━━━━━━━━━━━━━\n"
        text += f"📋 مێژووی دابەزاندن ({len(history)} دوایین):\n\n"
        if history:
            for i, (url, platform, downloaded_at) in enumerate(history, 1):
                date_str = str(downloaded_at)[:16] if downloaded_at else '-'
                platform_str = platform or 'نەزانراو'
                text += f"{i}. [{platform_str}] {date_str}\n{url}\n\n"
        else:
            text += "هیچ مێژوویەک نییە.\n"

        # Telegram has a 4096-char message limit — split if needed
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await update.message.reply_text(
                    text[i:i+4000],
                    disable_web_page_preview=True
                )
        else:
            await update.message.reply_text(text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in user_command: {e}")


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not _is_admin(update.effective_user.id):
            await update.message.reply_text(MESSAGES["broadcast_no_access"])
            return
        if not context.args:
            await update.message.reply_text(MESSAGES["ban_usage"])
            return
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(MESSAGES["ban_usage"])
            return
        success = ban_user(target_id)
        if success:
            await update.message.reply_text(MESSAGES["ban_success"].format(target_id))
        else:
            await update.message.reply_text(MESSAGES["ban_already"])
    except Exception as e:
        logger.error(f"Error in ban_command: {e}")


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not _is_admin(update.effective_user.id):
            await update.message.reply_text(MESSAGES["broadcast_no_access"])
            return
        if not context.args:
            await update.message.reply_text(MESSAGES["unban_usage"])
            return
        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(MESSAGES["unban_usage"])
            return
        success = unban_user(target_id)
        if success:
            await update.message.reply_text(MESSAGES["unban_success"].format(target_id))
        else:
            await update.message.reply_text(MESSAGES["unban_not_found"])
    except Exception as e:
        logger.error(f"Error in unban_command: {e}")


# ---------------------------------------------------------------------------
# Daily report job
# ---------------------------------------------------------------------------

async def send_daily_report(context: ContextTypes.DEFAULT_TYPE):
    try:
        admin_id = _get_admin_id()
        if not admin_id:
            return
        downloads, new_users, top_users = get_daily_stats()
        top_text = ""
        for i, (first_name, username, count) in enumerate(top_users, 1):
            name = first_name or username or "نەناسراو"
            top_text += f"{i}. {name} — {count} جار\n"
        text = MESSAGES["daily_report"].format(downloads, new_users, top_text or "—")
        await context.bot.send_message(chat_id=admin_id, text=text)
    except Exception as e:
        logger.error(f"Error in send_daily_report: {e}")


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

async def _handle_single_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Show format picker (Video / Audio) for a single non-YouTube URL."""
    user_id = update.effective_user.id
    url_key = f"dl_{user_id}_{uuid.uuid4().hex[:10]}"
    context.user_data[url_key] = url
    platform = _detect_platform(url)
    keyboard = [[
        InlineKeyboardButton(MESSAGES["format_video"], callback_data=f"dl_video_{url_key}"),
        InlineKeyboardButton(MESSAGES["format_audio"], callback_data=f"dl_audio_{url_key}"),
    ]]
    await update.message.reply_text(
        f"{MESSAGES['format_options']} ({platform})",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


async def _do_download_and_send(
    context,
    chat_id: int,
    url: str,
    format_type: str,
    processing_message,
    user_id: int,
    username: str,
    first_name: str,
):
    """Run the actual download and send logic for a non-YouTube URL."""
    loop = asyncio.get_event_loop()
    progress_hook, stop_hook = _make_progress_hook(loop, processing_message)
    platform = _detect_platform(url)

    try:
        if DOWNLOAD_SEMAPHORE.locked():
            try:
                await processing_message.edit_text(MESSAGES["queued"], disable_web_page_preview=True)
            except Exception:
                pass

        async with DOWNLOAD_SEMAPHORE:
            if format_type == 'audio':
                file_path, result = await asyncio.to_thread(
                    downloader.download_audio, url, progress_hook
                )
                completed_msg = MESSAGES["completed_audio_generic"]
            else:
                file_path, result = await asyncio.to_thread(
                    downloader.download_video, url, progress_hook
                )
                completed_msg = MESSAGES["completed"]

        # Stop the progress hook before touching the message
        stop_hook()

        if file_path:
            try:
                if format_type == 'audio':
                    await _send_audio_file(context, chat_id, file_path, completed_msg)
                else:
                    await _send_video_file(context, chat_id, file_path, completed_msg)
                record_download(user_id, username, first_name, url, platform)
            except (TimedOut, NetworkError) as e:
                # Upload likely reached Telegram despite the timeout — don't
                # send a false error message; just log and move on.
                logger.warning(f"Network/timeout error while sending file (file probably delivered): {e}")
                record_download(user_id, username, first_name, url, platform)
            except TelegramError as e:
                if "file is too big" in str(e).lower() and format_type != 'audio':
                    await context.bot.send_message(
                        chat_id, MESSAGES["compressing"], disable_web_page_preview=True
                    )
                    compressed = await asyncio.to_thread(downloader.compress_video, file_path)
                    if compressed:
                        try:
                            await _send_video_file(context, chat_id, compressed, completed_msg)
                            record_download(user_id, username, first_name, url, platform)
                        except Exception as ce:
                            await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
                            logger.error(f"Compressed send failed: {ce}")
                        finally:
                            downloader.cleanup_file(compressed)
                    else:
                        await context.bot.send_message(chat_id, MESSAGES["error_file_too_large"])
                else:
                    await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
            finally:
                downloader.cleanup_file(file_path)
        else:
            if result == "file_too_large":
                await context.bot.send_message(chat_id, MESSAGES["error_file_too_large"])
            elif result == "instagram_auth_required":
                await context.bot.send_message(chat_id, MESSAGES["error_instagram_auth_required"])
            elif result == "extract_failed" and "instagram.com" in url.lower():
                await context.bot.send_message(chat_id, MESSAGES["error_instagram_auth"])
            elif result == "unsupported_platform":
                await context.bot.send_message(chat_id, MESSAGES["error_unsupported"])
            else:
                await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
    finally:
        stop_hook()
        try:
            await processing_message.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main message handler
# ---------------------------------------------------------------------------

async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        if await _check_banned(update):
            return

        text = update.message.text.strip()
        user_id = update.effective_user.id

        urls = _extract_urls(text)
        if not urls:
            await update.message.reply_text(
                MESSAGES["no_url_found"], disable_web_page_preview=True
            )
            return

        supported = [u for u in urls if _is_supported(u)]
        if not supported:
            await update.message.reply_text(MESSAGES["error_unsupported"])
            return
        if len(supported) > BOT_MAX_BATCH_LINKS:
            await update.message.reply_text(
                MESSAGES["batch_limited"].format(BOT_MAX_BATCH_LINKS),
                disable_web_page_preview=True
            )
            supported = supported[:BOT_MAX_BATCH_LINKS]

        yt_urls = [u for u in supported if _is_youtube_url(u)]
        other_urls = [u for u in supported if not _is_youtube_url(u)]

        # YouTube: show quality picker
        for yt_url in yt_urls:
            url_key = f"yt_{user_id}_{uuid.uuid4().hex[:10]}"
            context.user_data[url_key] = yt_url
            keyboard = [
                [
                    InlineKeyboardButton(MESSAGES["youtube_v360"], callback_data=f"yt_video_360_{url_key}"),
                    InlineKeyboardButton(MESSAGES["youtube_v720"], callback_data=f"yt_video_720_{url_key}"),
                    InlineKeyboardButton(MESSAGES["youtube_v1080"], callback_data=f"yt_video_1080_{url_key}"),
                ],
                [InlineKeyboardButton(MESSAGES["youtube_audio_mp3"], callback_data=f"yt_audio_{url_key}")]
            ]
            await update.message.reply_text(
                MESSAGES["youtube_options"],
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )

        # Non-YouTube single: show Video/Audio picker
        if len(other_urls) == 1:
            await _handle_single_video(update, context, other_urls[0])
        elif len(other_urls) > 1:
            # Batch: download all as video automatically
            batch_msg = await update.message.reply_text(
                MESSAGES["batch_start"].format(len(other_urls)),
                disable_web_page_preview=True
            )
            for i, url in enumerate(other_urls, 1):
                try:
                    await batch_msg.edit_text(
                        MESSAGES["batch_item"].format(i, len(other_urls)),
                        disable_web_page_preview=True
                    )
                except Exception:
                    pass
                proc = await update.message.reply_text(
                    MESSAGES["processing"], disable_web_page_preview=True
                )
                await _do_download_and_send(
                    context, update.effective_chat.id, url, 'video', proc,
                    user_id, update.effective_user.username, update.effective_user.first_name
                )
            try:
                await batch_msg.delete()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Unexpected error in handle_video_link: {e}")
        try:
            await update.message.reply_text(MESSAGES["error_download_failed"])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Callback handlers
# ---------------------------------------------------------------------------

async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Video/Audio picker for non-YouTube platforms."""
    query = update.callback_query
    await query.answer()

    try:
        data = query.data
        user_id = update.effective_user.id
        chat_id = query.message.chat_id

        if is_banned(user_id):
            await query.edit_message_text(MESSAGES["banned_message"])
            return

        video_match = re.match(r'^dl_video_(.+)$', data)
        audio_match = re.match(r'^dl_audio_(.+)$', data)

        if video_match:
            url_key = video_match.group(1)
            format_type = 'video'
        elif audio_match:
            url_key = audio_match.group(1)
            format_type = 'audio'
        else:
            await query.edit_message_text(MESSAGES["error_download_failed"])
            return

        url = context.user_data.get(url_key)
        if not url:
            await query.edit_message_text("خەپە! ناتوانم URL بدۆزمەوە، تکایە دووبارە تاقی بکەوە")
            return

        await query.edit_message_text(
            MESSAGES["processing"], disable_web_page_preview=True
        )

        await _do_download_and_send(
            context, chat_id, url, format_type, query.message,
            user_id, update.effective_user.username, update.effective_user.first_name
        )
        context.user_data.pop(url_key, None)

    except Exception as e:
        logger.error(f"Error in handle_download_callback: {e}")
        try:
            await query.edit_message_text(MESSAGES["error_download_failed"])
        except Exception:
            pass


async def handle_youtube_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube format/quality selection callbacks."""
    query = update.callback_query
    await query.answer()

    try:
        data = query.data
        user_id = update.effective_user.id
        chat_id = query.message.chat_id
        loop = asyncio.get_event_loop()

        if is_banned(user_id):
            await query.edit_message_text(MESSAGES["banned_message"])
            return

        video_match = re.match(r'^yt_video_(360|720|1080)_(.+)$', data)
        audio_match = re.match(r'^yt_audio_(.+)$', data)

        if video_match:
            quality = video_match.group(1)
            url_key = video_match.group(2)
            format_type = 'video'
        elif audio_match:
            url_key = audio_match.group(1)
            format_type = 'audio'
            quality = None
        else:
            await query.edit_message_text(MESSAGES["error_download_failed"])
            return

        youtube_url = context.user_data.get(url_key)
        if not youtube_url:
            await query.edit_message_text("خەپە! ناتوانم URL بدۆزمەوە، تکایە دووبارە تاقی بکەوە")
            return

        proc_text = MESSAGES["processing_video"] if format_type == 'video' else MESSAGES["processing_audio"]
        completed_msg = MESSAGES["completed_video"] if format_type == 'video' else MESSAGES["completed_audio"]

        await query.edit_message_text(proc_text, disable_web_page_preview=True)

        progress_hook, stop_hook = _make_progress_hook(loop, query.message)

        if DOWNLOAD_SEMAPHORE.locked():
            try:
                await query.edit_message_text(MESSAGES["queued"], disable_web_page_preview=True)
            except Exception:
                pass

        async with DOWNLOAD_SEMAPHORE:
            file_path, result, quality_used = await asyncio.to_thread(
                downloader.download_youtube_with_fallback,
                youtube_url, format_type, quality or '1080', progress_hook
            )

        # Stop hook before any message operations
        stop_hook()

        if file_path:
            # If quality was downgraded, let the user know
            if format_type == 'video' and quality_used != quality:
                await context.bot.send_message(
                    chat_id,
                    MESSAGES["retry_lower_quality"],
                    disable_web_page_preview=True
                )
            try:
                if format_type == 'audio':
                    await _send_audio_file(context, chat_id, file_path, completed_msg)
                else:
                    await _send_video_file(context, chat_id, file_path, completed_msg)
                record_download(
                    user_id, update.effective_user.username,
                    update.effective_user.first_name, youtube_url, 'YouTube'
                )
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Network/timeout error while sending YouTube file (file probably delivered): {e}")
                record_download(
                    user_id, update.effective_user.username,
                    update.effective_user.first_name, youtube_url, 'YouTube'
                )
            except TelegramError as e:
                if "file is too big" in str(e).lower():
                    await context.bot.send_message(chat_id, MESSAGES["compressing"])
                    compressed = await asyncio.to_thread(downloader.compress_video, file_path)
                    if compressed:
                        try:
                            await _send_video_file(context, chat_id, compressed, completed_msg)
                            record_download(
                                user_id, update.effective_user.username,
                                update.effective_user.first_name, youtube_url, 'YouTube'
                            )
                        except Exception as ce:
                            await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
                            logger.error(f"Compressed send failed: {ce}")
                        finally:
                            downloader.cleanup_file(compressed)
                    else:
                        await context.bot.send_message(chat_id, MESSAGES["error_file_too_large"])
                else:
                    await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
            except Exception as e:
                await context.bot.send_message(chat_id, MESSAGES["error_download_failed"])
                logger.error(f"Error sending YouTube file: {e}")
            finally:
                downloader.cleanup_file(file_path)
                try:
                    await query.delete_message()
                except Exception:
                    pass
        else:
            await query.edit_message_text(MESSAGES["error_download_failed"])
            logger.error(f"YouTube download failed: {result}")

        context.user_data.pop(url_key, None)

    except Exception as e:
        logger.error(f"Unexpected error in handle_youtube_callback: {e}")
        try:
            await query.edit_message_text(MESSAGES["error_download_failed"])
        except Exception:
            pass
