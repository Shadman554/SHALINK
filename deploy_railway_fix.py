#!/usr/bin/env python3
"""
Direct test of YouTube downloads for Railway deployment
This script ensures YouTube downloads work before deployment
"""
import os
import sys
import tempfile
import subprocess

def test_youtube_download():
    """Test YouTube download functionality directly"""
    print("🔧 Testing YouTube download functionality...")
    
    try:
        # Import the video downloader
        from video_downloader import VideoDownloader
        
        # Test download
        downloader = VideoDownloader()
        test_url = "https://youtu.be/dQw4w9WgXcQ"  # Rick Roll - always available
        
        print(f"Testing video download for: {test_url}")
        video_file, video_result = downloader.download_youtube(test_url, 'video')
        
        if video_file and os.path.exists(video_file):
            file_size = os.path.getsize(video_file)
            print(f"✅ Video download SUCCESS: {file_size} bytes")
            # Clean up
            os.remove(video_file)
            return True
        else:
            print(f"❌ Video download FAILED: {video_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing YouTube download: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'telegram',
        'yt_dlp',
        'requests'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            return False
    
    return True

def check_ffmpeg():
    """Check if ffmpeg is available"""
    print("🎬 Checking ffmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ffmpeg available")
            return True
        else:
            print("❌ ffmpeg not working")
            return False
    except:
        print("❌ ffmpeg not found")
        return False

if __name__ == "__main__":
    print("🚀 Railway Deployment Test Starting...")
    print("=" * 50)
    
    # Run all checks
    deps_ok = check_dependencies()
    ffmpeg_ok = check_ffmpeg()
    youtube_ok = test_youtube_download()
    
    print("=" * 50)
    print("📋 Test Results:")
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"FFmpeg:       {'✅ PASS' if ffmpeg_ok else '❌ FAIL'}")
    print(f"YouTube:      {'✅ PASS' if youtube_ok else '❌ FAIL'}")
    
    if deps_ok and ffmpeg_ok and youtube_ok:
        print("\n🎉 ALL TESTS PASSED - RAILWAY DEPLOYMENT READY!")
        sys.exit(0)
    else:
        print("\n💥 TESTS FAILED - DEPLOYMENT NOT READY")
        sys.exit(1)