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
    "instagram.com/reel",
    "instagram.com/p/",
    "vm.tiktok.com",
    "vt.tiktok.com"
]

# Kurdish messages
MESSAGES = {
    "start": "تکایە لینکی ڤیدیۆکەت دابنێ",
    "processing": "ڤیدیۆکەت دادەبەزێت...",
    "completed": "فەرموو ئەوەش ڤیدیۆکەت",
    "error_invalid_link": "لینکەکە دروست نییە، تکایە لینکێکی دروست دابنێ",
    "error_download_failed": "ڕووداوێک ڕووی دا لە دابەزاندنی ڤیدیۆکە، تکایە دووبارە تاقی بکەوە",
    "error_unsupported": "ئەم لینکە پشتگیری ناکرێت، تکایە لینکی TikTok، Instagram یان Facebook بەکاربهێنە"
}

# Download settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit for Telegram
TEMP_DIR = "/tmp/telegram_bot_downloads"
