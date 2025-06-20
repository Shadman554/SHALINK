"""
Configuration file for the Telegram bot.
"""

import os

# Telegram Bot Token - get from environment or use provided token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7731476029:AAFF7g3M6hpqzQaQtv2djUkJfCfS8M08fxQ")

# Supported platforms
SUPPORTED_PLATFORMS = [
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "fb.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "www.instagram.com",
    "www.tiktok.com",
    "www.facebook.com"
]

# Kurdish messages
MESSAGES = {
    "start": "تکایە لینکی ڤیدیۆکەت دابنێ",
    "processing": "ڤیدیۆکەت دادەبەزێت...",
    "completed": "فەرموو ئەوەش ڤیدیۆکەت",
    "error_invalid_link": "لینکەکە دروست نییە، تکایە لینکێکی دروست دابنێ",
    "error_download_failed": "ڕووداوێک ڕووی دا لە دابەزاندنی ڤیدیۆکە، تکایە دووبارە تاقی بکەوە",
    "error_unsupported": "ئەم لینکە پشتگیری ناکرێت، تکایە لینکی TikTok، Instagram یان Facebook بەکاربهێنە",
    "error_instagram_auth": "Instagram ڤیدیۆکان پێویستیان بە چاوەڕوانی زیاترە، تکایە چەند چرکەیەک چاوەڕێ بە و دووبارە تاقی بکەوە",
    "error_instagram_auth_required": "Instagram ڤیدیۆ دابەزاندن پێویستی بە تۆماربوونە، تکایە دووبارە تاقی بکەوە یان لینکێکی TikTok بەکاربهێنە",
    "error_file_too_large": "ڤیدیۆکە زۆر گەورەیە، ناتوانرێت بنێردرێت"
}

# Download settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit for Telegram
TEMP_DIR = "/tmp/telegram_bot_downloads"
