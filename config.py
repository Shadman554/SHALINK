"""
Configuration file for the Telegram bot.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

SUPPORTED_PLATFORMS = [
    "tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "www.tiktok.com",
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "fb.com",
    "youtube.com",
    "youtu.be",
    "www.youtube.com",
    "m.youtube.com",
    "twitter.com",
    "www.twitter.com",
    "x.com",
    "www.x.com",
    "t.co",
    "pinterest.com",
    "www.pinterest.com",
    "pin.it",
    "pinterest.co.uk",
]

MESSAGES = {
    "start": (
        "بەخێربێیت بۆ بۆتی شا لینک! 👋\n"
        "لینکی ڤیدیۆکەت بنێرە و من دایدەبەزێنم.\n\n"
        "تایبەتمەندیەکان:\n"
        "١. بۆتەکەمان پشتگیری ئەم پلاتفۆرمانە دەکات:\n"
        "• TikTok  • Instagram  • Facebook\n"
        "• YouTube  • Twitter/X  • Pinterest\n\n"
        "٢. دەتوانیت چەند لینکیش لە یەک پەیامدا بنێریت.\n"
        "٣. دەتوانیت بە هەرسێ کوالێتی 360p-720p-1080p ڤیدیۆکان دابەزێنیت.\n"
        "٤. بۆ هەر ڤیدیۆیەک دەتوانی دەنگەکەی بەجیا بە شێوەی MP3 دابەزێنیت.\n"
        "٥. ڤیدیۆکانی تیکتۆک دەتوانیت بەبێ لۆگۆ داببەزێنیت.\n"
        "٦. کاتێک لە چاتی هاوڕێکەتی و دەتەوێت ڤیدیۆیەکی بۆ بنێریت پێویست ناکا بێێتە ناو بۆتەکەو ڤیدیۆکە داببەزێنیت و بۆی بنێریتەوە دەتوانی هەر بە نوسینی @shalink_bot پاشان دانانی لینکی ڤیدیۆکە راستەوخۆ لەناو چاتی هاوڕیکەت ڤیدیۆکە دادەبەزێت و دەیبینێت\n"
        "بۆ نموونە ئەمە دەنێریت بۆ هاوڕێکەت:\n\n"
        "@shalink_bot https://..... video link\n\n"
        "دەتوانیت لەڕێی ئەم کۆماندانەوە کۆمەڵێک زانیاری بزانیت:\n"
        "/start : بەکاردێ بۆ بینینی ئەم زانیاریانەی کە ئیستا دەیبینی\n"
        "/stats : پێت دەڵێت کە چەن ڤیدیۆت دابەزاندوە تائیستا چەن بەکارهێنەری هەیە بۆتەکە تائیستا\n"
        "/history : کۆتا ١٠ ڤیدیۆ کە داتبەزاندوە لەڕێی ئەم بۆتەوە هەموویت بۆ دەنێریتەوە"
    ),
    "processing": "⏳ چاوەڕێ بە...",
    "downloading": "⬇️ دادەبەزێت... {}%",
    "completed": "✅ فەرموو ئەوەش ڤیدیۆکەت",
    "error_invalid_link": "❌ لینکەکە دروست نییە، تکایە لینکێکی دروست دابنێ",
    "error_download_failed": "❌ ڕووداوێک ڕووی دا لە دابەزاندنی ڤیدیۆکە، تکایە دووبارە تاقی بکەوە",
    "error_unsupported": (
        "❌ ئەم لینکە پشتگیری ناکرێت.\n"
        "تکایە لینکی TikTok، Instagram، Facebook، YouTube، Twitter/X یان Pinterest بەکاربهێنە"
    ),
    "error_instagram_auth": "⚠️ Instagram ڤیدیۆکان پێویستیان بە چاوەڕوانی زیاترە، تکایە چەند چرکەیەک چاوەڕێ بە و دووبارە تاقی بکەوە",
    "error_instagram_auth_required": "⚠️ Instagram ڤیدیۆ دابەزاندن پێویستی بە تۆماربوونە، تکایە دووبارە تاقی بکەوە یان لینکێکی TikTok بەکاربهێنە",
    "error_file_too_large": "❌ ڤیدیۆکە زۆر گەورەیە، ناتوانرێت بنێردرێت",
    "youtube_options": "🎬 YouTube - کوالیتی هەڵبژێرە:",
    "youtube_v360": "📱 360p",
    "youtube_v720": "💻 720p",
    "youtube_v1080": "🖥️ 1080p",
    "youtube_audio_mp3": "🎵 MP3",
    "processing_video": "⬇️ ڤیدیۆ دادەبەزێت...",
    "processing_audio": "⬇️ دەنگ MP3 دادەبەزێت...",
    "completed_video": "✅ فەرموو ئەوەش ڤیدیۆکەت",
    "completed_audio": "✅ فەرموو ئەوەش فایلی دەنگەکەت",
    "compressing": "⚙️ ڤیدیۆکە زۆر گەورەیە، بچووک دەکرێتەوە...",
    "batch_start": "⬇️ {} لینک دیارکرا، دادەبەزێت...",
    "batch_item": "⬇️ ({}/{}) دادەبەزێت...",
    "stats_user": (
        "📊 ئامارەکانت:\n"
        "• دابەزاندن: {} جار\n"
        "• یەکەم جار بەکارهێنان: {}"
    ),
    "stats_global": "\n\n🌍 کۆی گشتی:\n• {} بەکارهێنەر  •  {} دابەزاندن",
    "stats_none": "📊 تا ئێستا هیچ ڤیدیۆیەکت دابەزاندووە.",
    "broadcast_usage": "⚙️ بەکارهێنان: /broadcast <پەیام>",
    "broadcast_no_access": "❌ تەنها ئەدمین دەتوانێت ئەم فەرمانە بەکاربهێنێت",
    "broadcast_done": "✅ پەیامەکە بۆ {} بەکارهێنەر نێردرا",
    "no_url_found": "❌ هیچ لینکێک نەدۆزرایەوە. تکایە لینکێکی دروست بنێرە",

    "format_options": "📥 ڕووپێوی هەڵبژێرە:",
    "format_video": "📹 ڤیدیۆ",
    "format_audio": "🎵 دەنگ MP3",
    "completed_audio_generic": "✅ فەرموو ئەوەش فایلی دەنگەکەت",

    "history_empty": "📋 تا ئێستا هیچ دابەزاندنێکت نییە.",
    "history_header": "📋 دوایین دابەزاندنەکانت:\n\n",

    "ban_usage": "⚙️ بەکارهێنان: /ban <user_id>",
    "ban_success": "✅ بەکارهێنەر بانکرا: {}",
    "ban_already": "⚠️ ئەم بەکارهێنەرە پێشتر بانکراوە",
    "unban_usage": "⚙️ بەکارهێنان: /unban <user_id>",
    "unban_success": "✅ بانی بەکارهێنەر لەبراوە: {}",
    "unban_not_found": "⚠️ ئەم بەکارهێنەرە بانکراو نییە",
    "banned_message": "❌ بەکارهێنانت بانکرا، ناتوانیت ئەم بۆتە بەکاربهێنیت",

    "user_usage": "⚙️ بەکارهێنان: /user <user_id>",
    "user_not_found": "❌ بەکارهێنەر نەدۆزرایەوە",
    "user_info": (
        "👤 زانیاری بەکارهێنەر:\n"
        "• ID: {}\n"
        "• ناو: {}\n"
        "• بەکارهێنەر: @{}\n"
        "• دابەزاندن: {} جار\n"
        "• یەکەم جار: {}\n"
        "• دوایین جار: {}"
    ),

    "daily_report": (
        "📊 ڕاپۆرتی ڕۆژانە:\n\n"
        "⬇️ دابەزاندنی ئەمڕۆ: {}\n"
        "👥 بەکارهێنەری نوێ: {}\n\n"
        "🏆 زیاترین دابەزاندن:\n{}"
    ),

    "retry_lower_quality": "⚠️ ڤیدیۆکە زۆر گەورەیە، کوالیتیی کەمتر تاقی دەکرێتەوە...",

    "inline_title": "⬇️ دابەزاندنی ڤیدیۆ",
    "inline_description": "لێرە دووکلیک بکە بۆ دابەزاندن",
    "inline_unsupported": "❌ لینکەکە پشتگیری ناکرێت",
}

INSTAGRAM_PROXY = os.getenv('INSTAGRAM_PROXY') or None

MAX_FILE_SIZE = 1000 * 1024 * 1024
TEMP_DIR = "/tmp/telegram_bot_downloads"
