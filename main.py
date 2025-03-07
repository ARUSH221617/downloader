import os
from dataclasses import dataclass
from typing import Optional, Callable
from urllib.parse import urlparse, parse_qs

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
        self.insta_loader = instaloader.Instaloader()
        self.spotify_client = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIPY_CLIENT_ID", "your_spotify_client_id"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET", "your_spotify_client_secret")
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
            shortcode = url.split("/")[-2]
            post = instaloader.Post.from_shortcode(self.insta_loader.context, shortcode)
            self.insta_loader.download_post(post, target='downloads')
            return DownloadResult(
                success=True,
                message=f"Downloaded Instagram post to downloads folder",
                data={"post_url": post.url}
            )
        except Exception as e:
            return DownloadResult(success=False, message=f"Instagram download failed: {str(e)}")

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

def main():
    st.set_page_config(
        page_title="Multi-Platform Downloader",
        page_icon="🌐",
        layout="centered"
    )

    st.title("🌐 Multi-Platform Downloader")
    
    # Add supported platforms info
    st.sidebar.title("Supported Platforms")
    platforms = ["YouTube", "Instagram", "TikTok", "Freepik", "Dribbble", "Spotify", "LottieFiles"]
    for platform in platforms:
        st.sidebar.markdown(f"- {platform}")

    url = st.text_input("Paste URL Here:", help="Enter the URL of the content you want to download")
    
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
            result = handler(url)
            
            if result.success:
                st.success(result.message)
                if result.data:
                    st.json(result.data)
            else:
                st.error(result.message)

if __name__ == "__main__":
    main()
