#!/usr/bin/env python3
"""
Test YouTube download functionality directly
"""
import os
import sys
from video_downloader import VideoDownloader

# Test the specific URL that's failing
test_url = "https://youtu.be/-pMeYPNaptk?si=m9QyFd2Vj8jvjdPJ"

print(f"Testing YouTube download for: {test_url}")

downloader = VideoDownloader()

# Test video download
print("\n=== Testing Video Download ===")
try:
    video_file, video_result = downloader.download_youtube(test_url, 'video')
    print(f"Video result: {video_result}")
    if video_file:
        print(f"Video file: {video_file}")
        print(f"Video file exists: {os.path.exists(video_file) if video_file else False}")
    else:
        print("Video download failed")
except Exception as e:
    print(f"Video download error: {e}")

# Test audio download
print("\n=== Testing Audio Download ===")
try:
    audio_file, audio_result = downloader.download_youtube(test_url, 'audio')
    print(f"Audio result: {audio_result}")
    if audio_file:
        print(f"Audio file: {audio_file}")
        print(f"Audio file exists: {os.path.exists(audio_file) if audio_file else False}")
    else:
        print("Audio download failed")
except Exception as e:
    print(f"Audio download error: {e}")