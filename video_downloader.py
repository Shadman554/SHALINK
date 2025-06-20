"""
Video downloader module using yt-dlp for TikTok, Instagram, and Facebook videos.
"""

import os
import tempfile
import yt_dlp
import logging
import base64
import pathlib
import tempfile
import json
from urllib.parse import urlparse
from config import SUPPORTED_PLATFORMS, MAX_FILE_SIZE, TEMP_DIR
import requests
import time

logger = logging.getLogger(__name__)

# ---- Decode cookie env vars into temp files (Railway safe method) ----
for env_var, out_name in (('IG_COOKIES_B64', 'instagram.txt'), ('FB_COOKIES_B64', 'facebook.txt')):
    b64_data = os.getenv(env_var)
    logger.info(f"{env_var} present: %s bytes", len(b64_data or ""))
    if b64_data:
        try:
            out_path = pathlib.Path(tempfile.gettempdir()) / out_name
            out_path.write_bytes(base64.b64decode(b64_data))
            # expose path to downstream logic
            os.environ[f"{env_var[:-4]}FILE"] = str(out_path)  # sets IG_COOKIES_FILE / FB_COOKIES_FILE
            logger.info(f"Decoded {env_var} to {out_path}")
        except Exception as e:
            logger.error(f"Failed to decode {env_var}: {e}")
# --------------------------------------------------------------------

class VideoDownloader:
    def __init__(self):
        """Initialize with persistent session support."""
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Enhanced Instagram cookie handling
        self.cookies_instagram = self._validate_cookies(
            os.getenv('IG_COOKIES_FILE'),
            os.path.join(os.getcwd(), "instagram_cookies.txt"),
            os.path.join(tempfile.gettempdir(), "instagram.txt")
        )
        
        # Base download options
        self.ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.instagram.com/'
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }
        
        # Instagram specific options
        self.instagram_opts = {
            'cookiefile': self.cookies_instagram,
            'extractor_args': {
                'instagram': {
                    'cookiefile': self.cookies_instagram,
                    'session': self._load_session() or None
                }
            }
        }
        
        # TikTok specific options - using dd01 API for watermark removal
        self.tiktok_opts = {
            'extractor': 'tiktok',
            'referer': 'https://www.tiktok.com/',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }
        
        # Alternative TikTok watermark removal API
        self.tiktok_api_url = "https://api.dd01.ru/api/tiktok?url="
        
    def _validate_cookies(self, *cookie_paths):
        """Validate and return first working cookie file with all required fields."""
        required_fields = ['sessionid', 'ds_user_id', 'csrftoken']
        for path in cookie_paths:
            if path and os.path.exists(path):
                try:
                    with open(path) as f:
                        content = f.read()
                        if all(field in content for field in required_fields):
                            return path
                except Exception:
                    continue
        return None
    
    def _load_session(self):
        """Load persistent session if exists."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    
    def _save_session(self, session):
        """Save session data persistently."""
        with open(self.session_file, 'w') as f:
            json.dump(session, f)
    
    def _setup_instagram_auth(self):
        """Comprehensive Instagram auth setup."""
        auth_methods = [
            self._try_cookie_auth,
            self._try_browser_auth,
            self._try_mobile_api_auth
        ]
        
        for method in auth_methods:
            if method():
                return True
        return False

    def _try_cookie_auth(self):
        """Try authenticating with provided cookies."""
        if not self.cookies_instagram:
            return False
            
        try:
            # Verify cookies contain required fields
            required = ['sessionid', 'ds_user_id', 'csrftoken']
            with open(self.cookies_instagram) as f:
                cookies = f.read()
                if not all(r in cookies for r in required):
                    return False
                    
            # Test authentication
            test_url = "https://www.instagram.com/accounts/edit/"
            with yt_dlp.YoutubeDL({
                'cookiefile': self.cookies_instagram,
                'quiet': True
            }) as ydl:
                info = ydl.extract_info(test_url, download=False)
                return bool(info)
        except Exception:
            return False

    def _try_browser_auth(self):
        """Try extracting fresh cookies from browser."""
        try:
            temp_opts = {
                'cookiesfrombrowser': ('chrome',),
                'quiet': True
            }
            with yt_dlp.YoutubeDL(temp_opts) as ydl:
                info = ydl.extract_info('https://www.instagram.com/', download=False)
                return bool(info)
        except Exception:
            return False

    def _try_mobile_api_auth(self):
        """Try mobile API authentication."""
        try:
            with yt_dlp.YoutubeDL({
                'http_headers': {
                    'User-Agent': 'Instagram 219.0.0.12.117 Android',
                    'X-IG-App-ID': '936619743392459'
                },
                'quiet': True
            }) as ydl:
                info = ydl.extract_info('https://www.instagram.com/', download=False)
                return bool(info)
        except Exception:
            return False
    
    def _setup_instagram_authentication(self):
        """Setup Instagram authentication using browser cookie extraction."""
        try:
            cookies_path = os.path.join(TEMP_DIR, 'instagram_cookies.txt')
            
            # Try to extract Instagram cookies from browser
            if self._try_extract_instagram_cookies(cookies_path):
                self.cookies_instagram = cookies_path
                logger.info("Instagram cookies extracted successfully")
            else:
                logger.info("Using alternative Instagram access method")
                self.cookies_instagram = None
                
        except Exception as e:
            logger.error(f"Instagram authentication setup failed: {e}")
            self.cookies_instagram = None
    
    def _try_extract_instagram_cookies(self, cookies_path: str) -> bool:
        """Try to extract Instagram cookies using yt-dlp's built-in browser cookie extraction."""
        try:
            # Use yt-dlp's built-in cookie extraction capability
            temp_opts = {
                'cookiesfrombrowser': ('chrome', None, None, None),
                'quiet': True,
                'no_warnings': True
            }
            
            # Attempt to extract cookies for Instagram
            with yt_dlp.YoutubeDL(temp_opts) as temp_ydl:
                # Test if we can extract cookies and access Instagram
                info = temp_ydl.extract_info('https://www.instagram.com/', download=False)
                if info:
                    # If successful, save these settings
                    return True
                    
        except Exception as e:
            logger.debug(f"Browser cookie extraction failed: {e}")
            
        # Try alternative browsers
        for browser in ['firefox', 'edge', 'safari']:
            try:
                temp_opts = {
                    'cookiesfrombrowser': (browser, None, None, None),
                    'quiet': True,
                    'no_warnings': True
                }
                
                with yt_dlp.YoutubeDL(temp_opts) as temp_ydl:
                    info = temp_ydl.extract_info('https://www.instagram.com/', download=False)
                    if info:
                        return True
                        
            except Exception:
                continue
                
        return False
    
    def is_supported_platform(self, url: str) -> bool:
        """Check if the URL is from a supported platform."""
        try:
            parsed_url = urlparse(url.lower())
            domain = parsed_url.netloc
            
            # Remove 'www.' prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return any(platform in domain for platform in SUPPORTED_PLATFORMS)
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return False
    
    def _download_instagram_video(self, url: str) -> tuple[str | None, str]:
        """Enhanced Instagram downloader with better cookie handling."""
        try:
            if not self.cookies_instagram:
                return None, "instagram_auth_required"
                
            ydl_opts = {**self.ydl_opts, **self.instagram_opts}
            
            # Try with cookies first
            for attempt in range(3):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            continue
                            
                        ydl.download([url])
                        title = info.get('title', 'instagram_video')
                        downloaded_file = self._find_downloaded_file(title)
                        
                        if downloaded_file and os.path.exists(downloaded_file):
                            return downloaded_file, title
                except Exception as e:
                    logger.warning(f"Instagram download attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        raise
                    time.sleep(1)
                    
            return None, "instagram_download_failed"
            
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return None, "instagram_download_failed"
            
    def _download_tiktok_video(self, url: str) -> tuple[str | None, str]:
        """TikTok downloader with watermark removal fallbacks."""
        try:
            # First try with direct API
            try:
                api_url = f"{self.tiktok_api_url}{url}"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    video_url = response.json().get('url')
                    if video_url:
                        return self._download_from_url(video_url, "tiktok_video")
            except Exception as api_error:
                logger.warning(f"TikTok API failed, falling back to yt-dlp: {api_error}")
            
            # Fallback to yt-dlp
            ydl_opts = {**self.ydl_opts, **self.tiktok_opts}
            
            for attempt in range(3):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            continue
                            
                        ydl.download([url])
                        title = info.get('title', 'tiktok_video')
                        downloaded_file = self._find_downloaded_file(title)
                        
                        if downloaded_file and os.path.exists(downloaded_file):
                            return downloaded_file, title
                except Exception as e:
                    logger.warning(f"TikTok download attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        raise
                    time.sleep(1)
                    
            return None, "tiktok_download_failed"
            
        except Exception as e:
            logger.error(f"TikTok download error: {e}")
            return None, "tiktok_download_failed"
    
    def _try_download(self, url: str, opts: dict) -> tuple[str | None, str]:
        """Try downloading video with given options."""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None, "extract_failed"
                
                title = info.get('title', 'video')
                
                # Check if file size is available and within limits
                filesize = info.get('filesize') or info.get('filesize_approx')
                if filesize and filesize > MAX_FILE_SIZE:
                    return None, "file_too_large"
                
                # Download the video
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(title)
                
                if downloaded_file and os.path.exists(downloaded_file):
                    # Check actual file size
                    if os.path.getsize(downloaded_file) > MAX_FILE_SIZE:
                        os.remove(downloaded_file)
                        return None, "file_too_large"
                    
                    return downloaded_file, title
                else:
                    return None, "download_failed"
                    
        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            return None, "download_failed"
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None, "download_failed"
    
    def download_video(self, url: str) -> tuple[str | None, str]:
        """
        Download video from the given URL.
        
        Returns:
            tuple: (file_path, title) if successful, (None, error_message) if failed
        """
        try:
            if not self.is_supported_platform(url):
                return None, "unsupported_platform"
            
            # Clean up any existing files in temp directory
            self._cleanup_temp_files()
            
            # Try Instagram-specific approach if it's an Instagram URL
            if 'instagram.com' in url:
                return self._download_instagram_video(url)
            
            # Try TikTok-specific approach if it's a TikTok URL
            if 'tiktok.com' in url:
                return self._download_tiktok_video(url)
            
            # Clone options so we don't mutate the shared dict
            ydl_opts = self.ydl_opts.copy()
            
            if any(site in url for site in ("facebook.com", "fb.com")) and self.cookies_facebook:
                ydl_opts["cookiefile"] = self.cookies_facebook

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get title and check file size
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None, "extract_failed"
                
                title = info.get('title', 'video')
                
                # Check if file size is available and within limits
                filesize = info.get('filesize') or info.get('filesize_approx')
                if filesize and filesize > MAX_FILE_SIZE:
                    return None, "file_too_large"
                
                # Download the video with retries
                for attempt in range(3):
                    try:
                        ydl.download([url])
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        time.sleep(1)
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(title)
                
                if downloaded_file and os.path.exists(downloaded_file):
                    # Check actual file size
                    if os.path.getsize(downloaded_file) > MAX_FILE_SIZE:
                        os.remove(downloaded_file)
                        return None, "file_too_large"
                    
                    return downloaded_file, title
                else:
                    return None, "download_failed"
                    
        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            return None, "download_failed"
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None, "download_failed"
    
    def _find_downloaded_file(self, title: str) -> str | None:
        """Find the downloaded file in the temp directory."""
        try:
            for file in os.listdir(TEMP_DIR):
                if file.startswith(title[:20]):  # Match first 20 chars of title
                    return os.path.join(TEMP_DIR, file)
            
            # If title-based search fails, get the newest file
            files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) if os.path.isfile(os.path.join(TEMP_DIR, f))]
            if files:
                return max(files, key=os.path.getctime)
            
            return None
        except Exception as e:
            logger.error(f"Error finding downloaded file: {e}")
            return None
    
    def _cleanup_temp_files(self):
        """Clean up temporary files older than 1 hour."""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        logger.info(f"Cleaned up old file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def cleanup_file(self, file_path: str):
        """Remove a specific file after use."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
