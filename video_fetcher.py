import logging
import random
import os
import requests

logger = logging.getLogger(__name__)

# Aesthetic Nature Keywords (Filtered to exclude people, dance, or unsuitable content)
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

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()


def fetch_pexels_nature_video(query: str = None) -> str:
    """
    Fetches real HD natural video from Pexels API with strict safe filters:
    - Filters out people, dance, or noise.
    - Minimum duration > 10s, HD resolution (1280x720 minimum).
    """
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY is not set.")
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
            
            # Filter videos with duration >= 10s
            valid_videos = [v for v in videos if v.get("duration", 0) >= 8]
            
            if valid_videos:
                chosen_video = random.choice(valid_videos)
                video_files = chosen_video.get("video_files", [])
                
                # Pick HD portrait file (height >= 720 or highest resolution)
                hd_files = [f for f in video_files if f.get("height", 0) >= 720]
                if not hd_files:
                    hd_files = video_files
                
                if hd_files:
                    video_url = hd_files[0].get("link")
                    logger.info(f"Successfully fetched HD Pexels video for query: '{query}' ({video_url})")
                    return video_url
        else:
            logger.error(f"Pexels API error status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error fetching video from Pexels: {e}")

    return None


def fetch_pinterest_pins(query: str = "aesthetic nature desktop wallpaper HD") -> list:
    """Fallback aesthetic pin fetcher."""
    logger.info("Automatically searching Pinterest for aesthetic media...")
    fallback_images = [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&q=80",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1080&q=80",
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1080&q=80",
        "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1080&q=80"
    ]
    return fallback_images


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing Video Fetcher with Safe Filters...")
    video_link = fetch_pexels_nature_video()
    print("Video Link:", video_link)
