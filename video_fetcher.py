import logging
import os
import random
import re
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# Curated aesthetic search queries for Pinterest & Pexels
AESTHETIC_QUERIES = [
    "aesthetic nature quiet",
    "peaceful rainy day aesthetic",
    "calm ocean waves aesthetic",
    "dark aesthetic nature silent",
    "starry night sky aesthetic",
    "foggy forest aesthetic",
    "autumn leaves aesthetic",
    "peaceful mountain clouds aesthetic"
]

PINTEREST_PUBLIC_BOARDS = [
    "https://www.pinterest.com/ideas/nature-aesthetic/928424269871/",
    "https://www.pinterest.com/ideas/dark-nature-aesthetic/917482819875/",
    "https://www.pinterest.com/ideas/calm-aesthetic/933827181045/"
]


def fetch_auto_pinterest_media(output_dir: str = ".") -> str | None:
    """
    Automatically finds and downloads aesthetic images/videos from Pinterest.
    """
    logger.info("Automatically searching Pinterest for aesthetic media...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        # Search Pinterest ideas / RSS
        query = random.choice(AESTHETIC_QUERIES)
        encoded_query = requests.utils.quote(query)
        search_url = f"https://www.pinterest.com/search/pins/?q={encoded_query}"

        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Extract high-res image URLs (pinimg.com domain)
            images = re.findall(r'https://i\.pinimg\.com/[0-9x]+/([a-zA-Z0-9/_.\-]+\.(?:jpg|jpeg|png))', response.text)
            if images:
                chosen_path = random.choice(images[:10])
                # Convert thumbnail to original 736x or originals high-res URL
                high_res_url = f"https://i.pinimg.com/736x/{chosen_path}"
                logger.info(f"Downloading Pinterest high-res pin: {high_res_url}")

                target_path = Path(output_dir) / "temp_pinterest_auto.jpg"
                res = requests.get(high_res_url, headers=headers, timeout=15)
                if res.status_code == 200:
                    with open(target_path, "wb") as f:
                        f.write(res.content)
                    return str(target_path)
    except Exception as e:
        logger.error(f"Error auto-searching Pinterest: {e}")

    return None


def fetch_natural_video(output_dir: str = ".") -> tuple[str | None, str]:
    """
    Fetches media file automatically:
    - 50% chance to fetch from Pinterest (Auto Aesthetic Pin)
    - 50% chance to fetch HD Real Nature Video from Pexels
    """
    choice = random.choice(["pinterest", "pexels"])

    if choice == "pinterest":
        pin_file = fetch_auto_pinterest_media(output_dir=output_dir)
        if pin_file:
            return pin_file, "photo"

    # Fallback / Pexels HD Video
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    if pexels_key:
        query = random.choice(AESTHETIC_QUERIES)
        logger.info(f"Fetching real natural video from Pexels for query: '{query}'...")
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
        headers = {"Authorization": pexels_key}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                if videos:
                    chosen_video = random.choice(videos[:5])
                    video_files = chosen_video.get("video_files", [])

                    best_file = None
                    for vf in video_files:
                        if vf.get("file_type") == "video/mp4":
                            if vf.get("width", 0) >= 720 or vf.get("height", 0) >= 720:
                                best_file = vf.get("link")
                                break

                    if not best_file and video_files:
                        best_file = video_files[0].get("link")

                    if best_file:
                        video_resp = requests.get(best_file, stream=True, timeout=30)
                        if video_resp.status_code == 200:
                            target_path = Path(output_dir) / "temp_natural_video.mp4"
                            with open(target_path, "wb") as f:
                                for chunk in video_resp.iter_content(chunk_size=1024 * 1024):
                                    if chunk:
                                        f.write(chunk)
                            return str(target_path), "video"
        except Exception as e:
            logger.error(f"Error fetching video from Pexels: {e}")

    # Fallback to Pinterest if Pexels didn't run
    pin_file = fetch_auto_pinterest_media(output_dir=output_dir)
    if pin_file:
        return pin_file, "photo"

    return None, "text"
