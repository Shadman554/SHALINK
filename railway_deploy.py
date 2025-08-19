#!/usr/bin/env python3
"""
Simple test to ensure Railway deployment works
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, '/app')

try:
    from video_downloader import VideoDownloader
    from bot_handlers import *
    from config import *
    
    print("✅ All imports successful")
    print("✅ VideoDownloader class available")
    print("✅ Bot handlers available")
    print("✅ Config loaded")
    
    # Test VideoDownloader initialization
    downloader = VideoDownloader()
    print("✅ VideoDownloader initialized successfully")
    
    print("🚀 Railway deployment ready!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)