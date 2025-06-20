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
        
        # Persistent session file
        self.session_file = os.path.join(TEMP_DIR, 'instagram_session.json')
        
        # Enhanced cookie handling
        self.cookies_instagram = self._validate_cookies(
            os.getenv('IG_COOKIES_FILE'), 
            os.path.join(os.getcwd(), "instagram_cookies.txt")
        )
        
        self.ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'cookiefile': self.cookies_instagram,
            'extractor_args': {
                'instagram': {
                    'cookiefile': self.cookies_instagram,
                    'session': self._load_session() or None
                }
            },
            'http_headers': {
                'User-Agent': 'Instagram 219.0.0.12.117 Android',
                'X-IG-App-ID': '936619743392459'
            }
        }
    
    def _validate_cookies(self, *cookie_paths):
        """Validate and return first working cookie file."""
        for path in cookie_paths:
            if path and os.path.exists(path):
                try:
                    with open(path) as f:
                        if 'sessionid' in f.read():
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
        """Download Instagram video with enhanced error handling."""
        
        # Verify cookies are valid before trying
        if self.cookies_instagram and not os.path.exists(self.cookies_instagram):
            logger.warning("Instagram cookie file not found, falling back to other methods")
            self.cookies_instagram = None
        
        # Try different Instagram extraction strategies
        strategies = [
            # Strategy 1: Use browser cookies if available
            {
                'cookiefile': self.cookies_instagram,
                'format': 'best[filesize<50M]/best',
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'extractor_args': {
                    'instagram': {
                        'api_hostname': 'i.instagram.com',
                        'include_stories': False,
                        'cookiefile': self.cookies_instagram
                    }
                }
            },
            # Strategy 2: Use mobile user agent
            {
                'format': 'best[filesize<50M]/best',
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'http_headers': {
                    'User-Agent': 'Instagram 219.0.0.12.117 Android (29/10; 300dpi; 720x1440; samsung; SM-A505F; a50; exynos9610; en_US; 331433749)',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'X-IG-App-ID': '936619743392459',
                    'X-ASBD-ID': '198387',
                    'X-IG-WWW-Claim': '0',
                    'Origin': 'https://www.instagram.com',
                    'Referer': 'https://www.instagram.com/',
                }
            },
            # Strategy 3: Fallback with basic settings
            {
                'format': 'worst[filesize<50M]/worst',
                'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
                'ignoreerrors': True,
                'no_warnings': True,
            }
        ]
        
        for i, strategy_opts in enumerate(strategies, 1):
            try:
                logger.info(f"Trying Instagram download strategy {i}")
                
                with yt_dlp.YoutubeDL(strategy_opts) as ydl:
                    # Extract info first
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        continue
                    
                    title = info.get('title', f'instagram_video_{i}')
                    
                    # Check file size
                    filesize = info.get('filesize') or info.get('filesize_approx')
                    if filesize and filesize > MAX_FILE_SIZE:
                        return None, "file_too_large"
                    
                    # Download the video
                    ydl.download([url])
                    
                    # Find the downloaded file
                    downloaded_file = self._find_downloaded_file(title)
                    
                    if downloaded_file:
                        logger.info(f"Instagram download successful with strategy {i}")
                        return downloaded_file, title
                        
            except Exception as e:
                logger.debug(f"Instagram strategy {i} failed: {e}")
                continue
        
        return None, "instagram_auth_required"
    
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
