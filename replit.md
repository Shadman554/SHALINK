# Telegram Video Downloader Bot

## Overview

This is a Telegram bot application that allows users to download videos from popular social media platforms including TikTok, Instagram, and Facebook. The bot responds in Kurdish language and provides a simple interface for users to share video links and receive downloaded content.

## System Architecture

### Backend Architecture
- **Language**: Python 3.11
- **Framework**: python-telegram-bot library for Telegram Bot API integration
- **Video Processing**: yt-dlp library for downloading videos from various platforms
- **Deployment**: Replit-based hosting with automated dependency installation

### Key Design Decisions
- **Modular Structure**: Separated concerns into distinct modules (handlers, downloader, config)
- **Asynchronous Processing**: Uses async/await pattern for non-blocking Telegram message handling
- **Error Handling**: Comprehensive error handling with user-friendly Kurdish messages
- **File Size Limitation**: 50MB limit to comply with Telegram's file size restrictions

## Key Components

### 1. Main Application (`main.py`)
- Entry point for the application
- Sets up Telegram bot with proper handlers
- Configures logging for monitoring and debugging

### 2. Bot Handlers (`bot_handlers.py`)
- `/start` command handler for user onboarding
- Message handler for processing video links
- Input validation and user feedback management

### 3. Video Downloader (`video_downloader.py`)
- Core downloading functionality using yt-dlp
- Platform validation for supported services
- File management and temporary storage handling

### 4. Configuration (`config.py`)
- Centralized configuration management
- Kurdish language message templates
- Platform support definitions and file size limits

## Data Flow

1. **User Input**: User sends a video link via Telegram
2. **Validation**: Bot validates URL format and platform support
3. **Processing**: Video downloader processes the link using yt-dlp
4. **Download**: Video is downloaded to temporary storage
5. **Delivery**: Video file is sent back to user via Telegram
6. **Cleanup**: Temporary files are managed to prevent storage issues

## External Dependencies

### Core Libraries
- **python-telegram-bot**: Telegram Bot API wrapper for Python
- **yt-dlp**: Video downloading library supporting multiple platforms
- **Standard Library**: logging, os, tempfile, urllib for utility functions

### Supported Platforms
- TikTok (tiktok.com, vm.tiktok.com, vt.tiktok.com)
- Instagram (instagram.com, instagram.com/reel, instagram.com/p/)
- Facebook (facebook.com, fb.com)

## Deployment Strategy

### Environment
- **Platform**: Replit with Python 3.11 runtime
- **Package Management**: UV lock file for dependency versioning
- **Auto-deployment**: Configured through .replit workflow automation

### Configuration
- Bot token management via environment variables with fallback
- Temporary file storage in `/tmp/telegram_bot_downloads`
- Parallel workflow execution for improved performance

### Scalability Considerations
- File size limitations prevent memory overflow
- Temporary storage cleanup to manage disk space
- Logging for monitoring bot performance and errors

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

✓ June 20, 2025: Successfully resolved package conflicts between python-telegram-bot and telegram stub package
✓ June 20, 2025: Bot is now running and responding to commands in Kurdish language
✓ June 20, 2025: Video downloading functionality tested and working for TikTok, Instagram, Facebook

## User Preferences

- Bot responses in Kurdish language as specified
- Fast performance with minimal delays
- Clean error handling without technical details exposed to users

## Changelog

Changelog:
- June 20, 2025. Initial setup and successful deployment