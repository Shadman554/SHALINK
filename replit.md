# Telegram Video Downloader Bot

## Overview

A Telegram bot that lets users download videos from TikTok, Instagram, Facebook, YouTube, Twitter/X, and Pinterest. All responses are in Kurdish.

## Architecture

- **Runtime**: Python 3.12 on Replit
- **Bot framework**: python-telegram-bot 20.8 with job-queue (APScheduler)
- **Downloader**: yt-dlp 2026.3.17+
- **Video processing**: ffmpeg-full system dependency via Replit Nix, plus imageio-ffmpeg Python package
- **Database**: PostgreSQL via `DATABASE_URL` (Replit built-in)
- **Replit workflow**: `Start application` runs `python main.py` as a console process
- **Replit deployment**: VM target running `python main.py` for an always-on Telegram polling bot
- **Reliability hardening**: per-download temporary folders prevent concurrent users from picking up each other's files; ffmpeg detection requires both `ffmpeg` and `ffprobe`; Telegram API URLs are no longer logged at INFO level to avoid exposing bot tokens; concurrent downloads are capped to protect Railway CPU/RAM; file downloads are capped to Telegram's upload limit before large files can fill disk.

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point — registers all handlers, starts scheduler |
| `bot_handlers.py` | All Telegram command and callback handlers |
| `video_downloader.py` | Download logic, audio extraction, YouTube auto-retry |
| `database.py` | PostgreSQL: users, history, bans, stats |
| `config.py` | Token, Kurdish messages, platform list |
| `requirements.txt` | Python dependencies |
| `.replit` | Replit runtime, workflow, Nix packages, and deployment configuration |

## Supported Platforms

TikTok, Instagram, Facebook, YouTube, Twitter/X, Pinterest

## Features

### For Users
- **Format picker** — every URL shows Video / MP3 Audio buttons (all platforms)
- **YouTube quality** — 360p / 720p / 1080p + MP3
- **Batch downloads** — send multiple links at once; bot downloads all as video
- **Live progress** — shows "⬇️ دادەبەزێت... 45%" during download

### For Admins
- **Daily report** — automatic message at 09:00 UTC with daily downloads + new users + top users
- **Broadcast** — `/broadcast <message>` to all users
- **User lookup** — `/user <id>` shows info and ban status
- **Ban / unban** — `/ban <id>` and `/unban <id>`

### Quality of life
- **Auto-retry lower quality** — if 1080p is too large, auto-retries 720p then 360p
- **Large video compression** — auto-compresses with ffmpeg before sending

## Commands

| Command | Who | Description |
|---------|-----|-------------|
| `/start` | Everyone | Welcome message |
| `/broadcast <msg>` | Admin | Send message to all users |
| `/user <id>` | Admin | Look up a user's stats and ban status |
| `/ban <id>` | Admin | Ban a user |
| `/unban <id>` | Admin | Unban a user |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `ADMIN_USER_ID` | Yes for admin commands | Your Telegram user ID for admin commands |
| `DATABASE_URL` | Yes | PostgreSQL connection string (auto-set by Replit) |
| `IG_COOKIES_B64` | Optional | Base64-encoded Instagram cookies |
| `FB_COOKIES_B64` | Optional | Base64-encoded Facebook cookies |
| `YT_COOKIES_B64` | Needed on server IPs | Base64-encoded YouTube cookies — required when hosting on Railway/Render/VPS to bypass YouTube bot-detection |
| `BOT_MAX_CONCURRENT_DOWNLOADS` | Optional | Max simultaneous downloads/uploads. Default `3`, recommended for Railway stability. |
| `BOT_MAX_BATCH_LINKS` | Optional | Max links accepted from one Telegram message. Default `10`. |
| `TELEGRAM_UPLOAD_LIMIT_MB` | Optional | Max downloaded file size before sending to Telegram. Default `48` MB. |

### How to get YouTube cookies (`YT_COOKIES_B64`)
1. Install the **"Get cookies.txt LOCALLY"** browser extension (Chrome/Firefox)
2. Open **youtube.com** and make sure you are logged in
3. Click the extension and export cookies for `youtube.com` — save as `youtube_cookies.txt`
4. Base64-encode the file: `base64 -w 0 youtube_cookies.txt` (Linux/Mac) or use an online encoder
5. Set the result as the `YT_COOKIES_B64` environment variable in your host (Railway / Replit secrets)

## Important Notes

- Only **one** bot instance can poll Telegram at a time. If you run this on Replit, stop any other deployments (Railway, etc.) using the same token, or they will conflict.
- Railway deployments install `ffmpeg-full` via `nixpacks.toml` so both `ffmpeg` and `ffprobe` are available. The Python `imageio-ffmpeg` package alone may provide `ffmpeg` but not `ffprobe`, which causes yt-dlp post-processing failures.
- `runtime.txt` uses `python-3.11.9` for Railway compatibility, while Replit uses Python 3.12 via `.replit`.
- If bot tokens appear in external logs or screenshots, rotate the Telegram token in @BotFather and update the secret.
