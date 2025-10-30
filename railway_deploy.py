#!/usr/bin/env python3
"""
Railway deployment helper - includes cookie encoding
"""
import sys
import os
import base64

def encode_cookies():
    """Encode instagram_cookies.txt to base64 for Railway."""
    cookie_file = 'instagram_cookies.txt'
    output_file = 'ig.b64'
    
    if not os.path.exists(cookie_file):
        print(f"⚠️  {cookie_file} not found, skipping encoding")
        return False
    
    try:
        with open(cookie_file, 'rb') as f:
            cookie_data = f.read()
        
        encoded = base64.b64encode(cookie_data).decode('ascii')
        
        with open(output_file, 'w') as f:
            f.write(encoded)
        
        print(f"✅ Encoded {len(cookie_data)} bytes to {output_file}")
        print(f"📋 Base64 preview: {encoded[:80]}...")
        return True
    except Exception as e:
        print(f"❌ Cookie encoding failed: {e}")
        return False

# Add current directory to path
sys.path.insert(0, '/app')

if __name__ == '__main__':
    print("="*60)
    print("Railway Deployment Helper")
    print("="*60)
    
    # Encode cookies if running locally
    if os.path.exists('instagram_cookies.txt'):
        print("\n🔐 Encoding Instagram cookies...")
        encode_cookies()
    
    print("\n🧪 Testing imports...")
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
        
        print("\n🚀 Railway deployment ready!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)