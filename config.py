"""
Configuration file for the Telegram bot.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token - get from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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

# Instagram Proxy Configuration (optional)
# Format: http://username:password@proxyip:port or http://proxyip:port
INSTAGRAM_PROXY = os.getenv('INSTAGRAM_PROXY') or None

# Proxy Rotation (if using multiple proxies)
PROXY_LIST = [
    # Add your proxy servers here
    # 'http://proxy1:port',
    # 'http://proxy2:port'
]

PROXY_ROTATION_ENABLED = False

# Download settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit for Telegram
TEMP_DIR = "/tmp/telegram_bot_downloads"
