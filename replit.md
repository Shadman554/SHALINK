# Telegram Video Downloader Bot

## Overview

A Telegram bot that lets users download videos from TikTok, Instagram, Facebook, YouTube, Twitter/X, and Pinterest. All responses are in Kurdish.

## Architecture

- **Runtime**: Python 3.12 on Replit
- **Bot framework**: python-telegram-bot 20.8 with job-queue (APScheduler)
- **Downloader**: yt-dlp 2026.3.17+
- **Video processing**: ffmpeg (system dependency via Nix)
- **Database**: SQLite (bot_data.db)

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point — registers all handlers, starts scheduler |
| `bot_handlers.py` | All Telegram command and callback handlers |
| `video_downloader.py` | Download logic, audio extraction, YouTube auto-retry |
| `database.py` | SQLite: users, history, bans, stats |
| `config.py` | Token, Kurdish messages, platform list |
| `requirements.txt` | Python dependencies |

## Supported Platforms

TikTok, Instagram, Facebook, YouTube, Twitter/X, Pinterest

## Features

### For Users
- **Format picker** — every URL shows Video / MP3 Audio buttons (all platforms)
- **YouTube quality** — 360p / 720p / 1080p + MP3
- **Batch downloads** — send multiple links at once; bot downloads all as video
- **Live progress** — shows "⬇️ دادەبەزێت... 45%" during download
- **Download history** — `/history` shows last 10 downloaded links
- **User stats** — `/stats` shows personal count + global totals
- **Inline mode** — type `@yourbot <url>` in any chat (requires BotFather `/setinline`)

### For Admins
- **Daily report** — automatic message at 09:00 UTC with daily downloads + new users + top users
- **Broadcast** — `/broadcast <message>` to all users
- **User lookup** — `/user <id>` shows info and ban status
- **Ban / unban** — `/ban <id>` and `/unban <id>`

### Quality of life
- **Auto-retry lower quality** — if 1080p is too large, auto-retries 720p then 360p
- **Link preview suppression** — processing messages never show ugly link previews
- **Large video compression** — auto-compresses with ffmpeg before sending

## Commands

| Command | Who | Description |
|---------|-----|-------------|
| `/start` | Everyone | Welcome message |
| `/stats` | Everyone | Personal + global download counts |
| `/history` | Everyone | Last 10 downloaded URLs |
| `/broadcast <msg>` | Admin | Send message to all users |
| `/user <id>` | Admin | Look up a user's stats and ban status |
| `/ban <id>` | Admin | Ban a user |
| `/unban <id>` | Admin | Unban a user |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `ADMIN_USER_ID` | Yes | Your Telegram user ID for admin commands |
| `IG_COOKIES_B64` | Optional | Base64-encoded Instagram cookies |
| `FB_COOKIES_B64` | Optional | Base64-encoded Facebook cookies |

## Enabling Inline Mode

To allow `@yourbot <url>` in any chat:
1. Open @BotFather → `/setinline` → select your bot
2. Set a placeholder text (e.g. "paste a video link…")
3. Done — inline mode is now active
