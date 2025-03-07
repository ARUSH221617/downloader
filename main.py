import streamlit as st
from urllib.parse import urlparse, parse_qs
import pytube
import instaloader
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Initialize Instaloader
L = instaloader.Instaloader()

# Setup Spotify credentials (replace with your own)
os.environ["SPOTIPY_CLIENT_ID"] = "your_spotify_client_id"
os.environ["SPOTIPY_CLIENT_SECRET"] = "your_spotify_client_secret"

# Function to detect platform
def detect_platform(url):
    domain = urlparse(url).netloc.lower()
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'YouTube'
    elif 'instagram.com' in domain:
        return 'Instagram'
    elif 'tiktok.com' in domain:
        return 'TikTok'
    elif 'freepik.com' in domain:
        return 'Freepik'
    elif 'dribbble.com' in domain:
        return 'Dribbble'
    elif 'spotify.com' in domain:
        return 'Spotify'
    elif 'lottiefiles.com' in domain:
        return 'LottieFiles'
    else:
        return None

# Downloaders
def download_youtube(url):
    try:
        yt = pytube.YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download()
        return f"Downloaded: {stream.default_filename}"
    except Exception as e:
        return f"Error: {str(e)}"

def download_instagram(url):
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target='')
        return f"Downloaded: {post.url}"
    except Exception as e:
        return f"Error: {str(e)}"

def download_tiktok(url):
    try:
        # Simple example, may not work due to anti-scraping measures
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        video_url = soup.find('video')['src']
        return f"Video URL: {video_url}"
    except Exception as e:
        return f"Error: {str(e)}"

def download_freepik(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_url = soup.find('img', class_='preview-image')['src']
        return f"Image URL: {img_url}"
    except Exception as e:
        return f"Error: {str(e)}"

def download_dribbble(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_url = soup.find('img', class_='Prose-image')['src']
        return f"Image URL: {img_url}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_spotify_info(url):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    track_id = parse_qs(urlparse(url).query).get('si', [None])[0]
    if not track_id:
        track_id = urlparse(url).path.split('/')[-1]
    track = sp.track(track_id)
    return f"Track: {track['name']} by {track['artists'][0]['name']}"

def download_lottie(url):
    try:
        response = requests.get(url)
        if response.status_code == 200 and 'application/json' in response.headers['content-type']:
            return "Lottie JSON downloaded successfully"
        else:
            return "Invalid Lottie URL"
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit App
st.title("🌐 Multi-Platform Downloader")
url = st.text_input("Paste URL Here:")
if st.button("Download"):
    platform = detect_platform(url)
    if not platform:
        st.error("Unsupported platform or invalid URL")
    else:
        try:
            if platform == 'YouTube':
                result = download_youtube(url)
            elif platform == 'Instagram':
                result = download_instagram(url)
            elif platform == 'TikTok':
                result = download_tiktok(url)
            elif platform == 'Freepik':
                result = download_freepik(url)
            elif platform == 'Dribbble':
                result = download_dribbble(url)
            elif platform == 'Spotify':
                result = get_spotify_info(url)
            elif platform == 'LottieFiles':
                result = download_lottie(url)
            else:
                result = "Platform not implemented yet"
            st.success(result)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")