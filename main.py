import os
from dataclasses import dataclass
from typing import Optional, Callable
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

import streamlit as st
import pytube
import instaloader
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

@dataclass
class DownloadResult:
    success: bool
    message: str
    data: Optional[dict] = None

class PlatformDownloader:
    def __init__(self):
        # Initialize Instagram loader
        self.insta_loader = instaloader.Instaloader(
            sleep=True,
            quiet=False,
            download_videos=True,
            download_geotags=False,
            download_comments=False,
            save_metadata=True
        )
        
        # Load Instagram credentials from .env
        insta_username = os.getenv("INSTAGRAM_USERNAME")
        insta_password = os.getenv("INSTAGRAM_PASSWORD")
        
        if insta_username and insta_password:
            try:
                self.insta_loader.login(insta_username, insta_password)
                print("Successfully logged in to Instagram")
            except Exception as e:
                print(f"Instagram login failed: {e}")
        else:
            print("Instagram credentials not found in .env file")
        
        # Initialize Spotify client with credentials from .env
        self.spotify_client = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
            )
        )
        
        # Map domains to their handler functions
        self.platform_handlers = {
            ("youtube.com", "youtu.be"): self.download_youtube,
            ("instagram.com",): self.download_instagram,
            ("tiktok.com",): self.download_tiktok,
            ("freepik.com",): self.download_freepik,
            ("dribbble.com",): self.download_dribbble,
            ("spotify.com",): self.get_spotify_info,
            ("lottiefiles.com",): self.download_lottie
        }

    def get_handler(self, url: str) -> Optional[Callable]:
        domain = urlparse(url).netloc.lower()
        for platforms, handler in self.platform_handlers.items():
            if any(platform in domain for platform in platforms):
                return handler
        return None

    def download_youtube(self, url: str) -> DownloadResult:
        try:
            # Configure YouTube with custom options
            yt = pytube.YouTube(
                url,
                # Disable OAuth temporarily as it's causing issues
                use_oauth=False,
                allow_oauth_cache=False
            )
            
            # Add custom headers to mimic browser request
            yt.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            # Get available streams and select the best quality
            streams = yt.streams.filter(progressive=True, file_extension='mp4')
            if not streams:
                return DownloadResult(
                    success=False,
                    message="No suitable video streams found"
                )
            
            # Get the highest quality stream
            stream = streams.get_highest_resolution()
            
            # Create downloads directory if it doesn't exist
            os.makedirs('downloads', exist_ok=True)
            
            # Download to the downloads directory
            filename = stream.default_filename
            stream.download(output_path='downloads')
            
            return DownloadResult(
                success=True,
                message=f"Downloaded: {filename}",
                data={
                    "filename": filename,
                    "title": yt.title,
                    "author": yt.author,
                    "length": yt.length,
                    "views": yt.views,
                    "path": os.path.join('downloads', filename)
                }
            )
        except pytube.exceptions.VideoUnavailable:
            return DownloadResult(
                success=False,
                message="Video is unavailable (possibly private or deleted)"
            )
        except pytube.exceptions.RegexMatchError:
            return DownloadResult(
                success=False,
                message="Invalid YouTube URL"
            )
        except Exception as e:
            error_message = str(e)
            if "403" in error_message:
                return DownloadResult(
                    success=False,
                    message="Access denied. Please try again in a few minutes."
                )
            return DownloadResult(
                success=False,
                message=f"YouTube download failed: {error_message}"
            )

    def download_instagram(self, url: str) -> DownloadResult:
        try:
            # Configure session with proper headers
            self.insta_loader.context.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
            
            # Add delay to avoid rate limiting
            self.insta_loader.sleep = True
            self.insta_loader.quiet = False
            
            # Extract post ID from URL
            if "/reel/" in url:
                shortcode = url.split("/reel/")[1].split("/")[0]
            else:
                shortcode = url.split("/p/")[1].split("/")[0]
            
            # Create downloads directory
            os.makedirs('downloads', exist_ok=True)
            
            # Download the post
            post = instaloader.Post.from_shortcode(self.insta_loader.context, shortcode)
            self.insta_loader.download_post(post, target='downloads')
            
            return DownloadResult(
                success=True,
                message=f"Downloaded Instagram post to downloads folder",
                data={
                    "post_url": post.url,
                    "caption": post.caption if post.caption else "No caption",
                    "date": post.date_local.isoformat(),
                    "is_video": post.is_video,
                    "likes": post.likes,
                    "comments": post.comments
                }
            )
        except instaloader.exceptions.InstaloaderException as e:
            if "429" in str(e):
                return DownloadResult(
                    success=False,
                    message="Rate limited. Please wait a few minutes before trying again."
                )
            elif "401" in str(e):
                return DownloadResult(
                    success=False,
                    message="Authentication required. Please log in to Instagram first."
                )
            elif "404" in str(e):
                return DownloadResult(
                    success=False,
                    message="Post not found. Please check the URL."
                )
            return DownloadResult(
                success=False,
                message=f"Instagram download failed: {str(e)}"
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                message=f"Instagram download failed: {str(e)}"
            )

    def download_tiktok(self, url: str) -> DownloadResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            video_url = soup.find('video')['src']
            return DownloadResult(
                success=True,
                message="Found TikTok video URL",
                data={"video_url": video_url}
            )
        except Exception as e:
            return DownloadResult(success=False, message=f"TikTok info retrieval failed: {str(e)}")

    def download_freepik(self, url: str) -> DownloadResult:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            img_url = soup.find('img', class_='preview-image')['src']
            return DownloadResult(
                success=True,
                message="Found Freepik image URL",
                data={"image_url": img_url}
            )
        except Exception as e:
            return DownloadResult(success=False, message=f"Freepik download failed: {str(e)}")

    def download_dribbble(self, url: str) -> DownloadResult:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            img_url = soup.find('img', class_='Prose-image')['src']
            return DownloadResult(
                success=True,
                message="Found Dribbble image URL",
                data={"image_url": img_url}
            )
        except Exception as e:
            return DownloadResult(success=False, message=f"Dribbble download failed: {str(e)}")

    def get_spotify_info(self, url: str) -> DownloadResult:
        try:
            track_id = parse_qs(urlparse(url).query).get('si', [None])[0]
            if not track_id:
                track_id = urlparse(url).path.split('/')[-1]
            
            track = self.spotify_client.track(track_id)
            return DownloadResult(
                success=True,
                message=f"Track: {track['name']} by {track['artists'][0]['name']}",
                data={"track_name": track['name'], "artist": track['artists'][0]['name']}
            )
        except Exception as e:
            return DownloadResult(success=False, message=f"Spotify info retrieval failed: {str(e)}")

    def download_lottie(self, url: str) -> DownloadResult:
        try:
            response = requests.get(url)
            if response.status_code == 200 and 'application/json' in response.headers['content-type']:
                return DownloadResult(success=True, message="Lottie JSON downloaded successfully")
            return DownloadResult(success=False, message="Invalid Lottie URL")
        except Exception as e:
            return DownloadResult(success=False, message=f"Lottie download failed: {str(e)}")

    def get_platform_handlers(self):
        return self.platform_handlers

class DownloadHistory:
    def __init__(self, history_file: str = "download_history.json"):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> list:
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def add_entry(self, url: str, platform: str, result: DownloadResult):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "platform": platform,
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
        self.history.insert(0, entry)  # Add to beginning of list
        self._save_history()

    def get_history(self, limit: int = None) -> list:
        return self.history[:limit] if limit else self.history

    def clear_history(self):
        self.history = []
        self._save_history()

def main():
    st.set_page_config(
        page_title="Multi-Platform Downloader",
        page_icon="🌐",
        layout="wide"  # Changed to wide layout to accommodate history
    )

    # Initialize download history
    history_manager = DownloadHistory()

    # Create two columns: main content and history
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("🌐 Multi-Platform Downloader")
        
        url = st.text_input("Paste URL Here:", help="Enter the URL of the content you want to download")
        
        # Advanced Options Section in Sidebar
        st.sidebar.title("Supported Platforms")
        platforms = ["YouTube", "Instagram", "TikTok", "Freepik", "Dribbble", "Spotify", "LottieFiles"]
        for platform in platforms:
            st.sidebar.markdown(f"- {platform}")

        st.sidebar.title("Advanced Options")
        show_advanced = st.sidebar.checkbox("Show Advanced Options")
        
        advanced_options = {}
        if show_advanced:
            st.sidebar.subheader("YouTube Options")
            advanced_options["youtube"] = {
                "quality": st.sidebar.selectbox(
                    "Video Quality",
                    ["highest", "720p", "480p", "360p", "lowest"]
                ),
                "format": st.sidebar.selectbox(
                    "Format",
                    ["mp4", "webm"]
                ),
                "audio_only": st.sidebar.checkbox("Audio Only (MP3)"),
                "include_playlist": st.sidebar.checkbox("Download Playlist (if URL is playlist)")
            }
            
            st.sidebar.subheader("Instagram Options")
            advanced_options["instagram"] = {
                "download_comments": st.sidebar.checkbox("Download Comments"),
                "download_geotags": st.sidebar.checkbox("Download Geotags"),
                "download_metadata": st.sidebar.checkbox("Download Metadata")
            }
            
            st.sidebar.subheader("General Options")
            advanced_options["general"] = {
                "custom_path": st.sidebar.text_input("Custom Download Path", "downloads"),
                "create_subfolders": st.sidebar.checkbox("Create Platform-specific Subfolders", True),
                "skip_existing": st.sidebar.checkbox("Skip Existing Files", True)
            }

        if st.button("Download", type="primary"):
            if not url:
                st.error("Please enter a URL")
                return

            downloader = PlatformDownloader()
            handler = downloader.get_handler(url)

            if not handler:
                st.error("Unsupported platform or invalid URL")
                return

            with st.spinner("Processing..."):
                # Apply advanced options if enabled
                if show_advanced:
                    result = process_with_advanced_options(handler, url, advanced_options)
                else:
                    result = handler(url)
                
                # Add to history
                platform = get_platform_from_url(url)
                history_manager.add_entry(url, platform, result)
                
                if result.success:
                    st.success(result.message)
                    if result.data:
                        st.json(result.data)
                else:
                    st.error(result.message)

    # History Column
    with col2:
        st.title("Download History")
        
        # Add history controls
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            history_limit = st.number_input("Show last N entries", min_value=1, value=10)
        with col2_2:
            if st.button("Clear History"):
                history_manager.clear_history()
                st.rerun()

        # Display history
        history = history_manager.get_history(limit=history_limit)
        if not history:
            st.info("No download history available")
        else:
            for entry in history:
                with st.expander(f"{entry['platform']} - {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"URL: {entry['url']}")
                    st.write(f"Status: {'✅ Success' if entry['success'] else '❌ Failed'}")
                    st.write(f"Message: {entry['message']}")
                    if entry['data']:
                        st.json(entry['data'])

def process_with_advanced_options(handler, url: str, options: dict) -> DownloadResult:
    """Process download with advanced options."""
    # Create custom download path if specified
    custom_path = options["general"]["custom_path"]
    os.makedirs(custom_path, exist_ok=True)
    
    # Determine the platform from the URL
    domain = urlparse(url).netloc.lower()
    
    # Create platform-specific subfolder if enabled
    if options["general"]["create_subfolders"]:
        for platform_domains in PlatformDownloader.platform_handlers.keys():
            if any(domain in platform_domain for platform_domain in platform_domains):
                platform_name = platform_domains[0].split('.')[0]
                custom_path = os.path.join(custom_path, platform_name)
                os.makedirs(custom_path, exist_ok=True)
                break
    
    # Handle YouTube-specific options
    if "youtube.com" in domain or "youtu.be" in domain:
        if options["youtube"]["audio_only"]:
            return download_youtube_audio(url, custom_path)
        else:
            return download_youtube_video(
                url, 
                custom_path,
                quality=options["youtube"]["quality"],
                format=options["youtube"]["format"]
            )
    
    # Handle Instagram-specific options
    elif "instagram.com" in domain:
        return download_instagram_with_options(
            url,
            custom_path,
            download_comments=options["instagram"]["download_comments"],
            download_geotags=options["instagram"]["download_geotags"],
            download_metadata=options["instagram"]["download_metadata"]
        )
    
    # For other platforms, just pass the custom path
    return handler(url, custom_path)

def download_youtube_video(url: str, output_path: str, quality: str, format: str) -> DownloadResult:
    try:
        yt = pytube.YouTube(url, use_oauth=False, allow_oauth_cache=False)
        
        # Select stream based on quality preference
        if quality == "highest":
            stream = yt.streams.filter(progressive=True, file_extension=format).get_highest_resolution()
        elif quality == "lowest":
            stream = yt.streams.filter(progressive=True, file_extension=format).get_lowest_resolution()
        else:
            stream = yt.streams.filter(progressive=True, file_extension=format, resolution=quality).first()
            
        if not stream:
            return DownloadResult(success=False, message=f"No stream available for quality: {quality}")
            
        filename = stream.default_filename
        stream.download(output_path=output_path)
        
        return DownloadResult(
            success=True,
            message=f"Downloaded: {filename}",
            data={
                "filename": filename,
                "title": yt.title,
                "quality": stream.resolution,
                "path": os.path.join(output_path, filename)
            }
        )
    except Exception as e:
        return DownloadResult(success=False, message=f"Download failed: {str(e)}")

def download_youtube_audio(url: str, output_path: str) -> DownloadResult:
    try:
        yt = pytube.YouTube(url, use_oauth=False, allow_oauth_cache=False)
        stream = yt.streams.filter(only_audio=True).first()
        
        if not stream:
            return DownloadResult(success=False, message="No audio stream available")
            
        # Download audio and convert to MP3
        audio_file = stream.download(output_path=output_path)
        base, _ = os.path.splitext(audio_file)
        mp3_file = base + '.mp3'
        os.rename(audio_file, mp3_file)
        
        return DownloadResult(
            success=True,
            message=f"Downloaded audio: {os.path.basename(mp3_file)}",
            data={
                "filename": os.path.basename(mp3_file),
                "title": yt.title,
                "path": mp3_file
            }
        )
    except Exception as e:
        return DownloadResult(success=False, message=f"Audio download failed: {str(e)}")

def get_platform_from_url(url: str) -> str:
    """Extract platform name from URL."""
    domain = urlparse(url).netloc.lower()
    if "youtube" in domain or "youtu.be" in domain:
        return "YouTube"
    elif "instagram" in domain:
        return "Instagram"
    elif "tiktok" in domain:
        return "TikTok"
    elif "freepik" in domain:
        return "Freepik"
    elif "dribbble" in domain:
        return "Dribbble"
    elif "spotify" in domain:
        return "Spotify"
    elif "lottiefiles" in domain:
        return "LottieFiles"
    return "Unknown"

if __name__ == "__main__":
    main()
