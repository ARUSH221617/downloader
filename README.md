# Multi-Platform Downloader

A Streamlit-based web application that allows users to download content from various platforms including YouTube, Instagram, TikTok, Freepik, Dribbble, Spotify, and LottieFiles.

## Features

- YouTube video downloads
- Instagram post downloads
- TikTok video information retrieval
- Freepik image downloads
- Dribbble image downloads
- Spotify track information
- LottieFiles JSON downloads

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd multi-platform-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Spotify API credentials:
   - Get your Spotify API credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Set your credentials in `main.py`:
     ```python
     os.environ["SPOTIPY_CLIENT_ID"] = "your_spotify_client_id"
     os.environ["SPOTIPY_CLIENT_SECRET"] = "your_spotify_client_secret"
     ```

## Configuration

1. Copy the template environment file:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` file with your credentials:
   ```env
   # Instagram credentials
   INSTAGRAM_USERNAME=your_username
   INSTAGRAM_PASSWORD=your_password

   # Spotify API credentials
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   ```

Note: The `.env` file is ignored by git for security purposes. Never commit your credentials to version control.

## Instagram Configuration

To download from Instagram, you can optionally set up authentication:

1. Set environment variables:
   ```bash
   export INSTAGRAM_USERNAME="your_username"
   export INSTAGRAM_PASSWORD="your_password"
   ```

2. Or create a `.env` file:
   ```
   INSTAGRAM_USERNAME=your_username
   INSTAGRAM_PASSWORD=your_password
   ```

Note: Without authentication, some posts might not be accessible due to Instagram's restrictions.

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Open your web browser and navigate to the provided local URL (typically `http://localhost:8501`)

3. Paste the URL of the content you want to download

4. Click the "Download" button

## Supported Platforms

- YouTube (`youtube.com`, `youtu.be`)
- Instagram (`instagram.com`)
- TikTok (`tiktok.com`)
- Freepik (`freepik.com`)
- Dribbble (`dribbble.com`)
- Spotify (`spotify.com`)
- LottieFiles (`lottiefiles.com`)

## Requirements

- Python 3.6+
- See `requirements.txt` for package dependencies

## Limitations

- TikTok downloads may be limited due to anti-scraping measures
- Some platforms may require authentication for certain content
- Download speeds may vary based on network conditions and platform restrictions

## License

[Add your chosen license here]

## Disclaimer

This tool is for educational purposes only. Please respect the terms of service of each platform and ensure you have the right to download content before using this tool.
