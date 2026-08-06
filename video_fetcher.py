import logging
import random
import os
import requests

logger = logging.getLogger(__name__)

SAFE_NATURE_QUERIES = [
    "calm ocean waves",
    "peaceful mountain clouds",
    "gentle forest rain",
    "serene sunrise horizon",
    "autumn leaves nature",
    "misty mountain forest",
    "starry night sky nature",
    "green meadow breeze"
]

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "yGiTash67DOp0P7TjqC8xUJEP30B9v1Lvx9fMc6VVMYFthFnVWpB9BY3").strip()


def fetch_pexels_nature_video(query: str = None) -> str:
    """Fetches real HD natural video from Pexels API with strict safe nature filters."""
    if not PEXELS_API_KEY:
        return None

    if not query:
        query = random.choice(SAFE_NATURE_QUERIES)

    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            valid_videos = [v for v in videos if v.get("duration", 0) >= 8]
            
            if valid_videos:
                chosen_video = random.choice(valid_videos)
                video_files = chosen_video.get("video_files", [])
                hd_files = [f for f in video_files if f.get("height", 0) >= 720]
                if not hd_files:
                    hd_files = video_files
                
                if hd_files:
                    return hd_files[0].get("link")
    except Exception as e:
        logger.error(f"Error fetching video from Pexels: {e}")

    return None
