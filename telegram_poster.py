import logging
import os
import requests
from telegram import Bot
from config import BOT_TOKEN, CHANNEL_ID
from video_fetcher import fetch_pexels_nature_video

logger = logging.getLogger(__name__)


async def send_post_to_channel(post_html: str, attach_media: bool = True) -> bool:
    """Sends published post to channel with optional HD nature video."""
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("Missing BOT_TOKEN or CHANNEL_ID.")
        return False

    bot = Bot(token=BOT_TOKEN)

    try:
        video_url = fetch_pexels_nature_video() if attach_media else None

        if video_url:
            logger.info("Downloading HD Pexels video...")
            v_resp = requests.get(video_url, timeout=15)
            if v_resp.status_code == 200:
                temp_video_path = "temp_natural_video.mp4"
                with open(temp_video_path, "wb") as f:
                    f.write(v_resp.content)

                with open(temp_video_path, "rb") as video_file:
                    await bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=video_file,
                        caption=post_html,
                        parse_mode="HTML"
                    )

                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

                logger.info("Successfully published post with HD Video.")
                return True

        # Fallback text post
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_html,
            parse_mode="HTML"
        )
        logger.info("Successfully published HTML text post.")
        return True
    except Exception as e:
        logger.error(f"Error posting to channel: {e}")
        return False
