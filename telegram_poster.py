import logging
import os
from telegram import Bot
from telegram.error import TelegramError
from config import BOT_TOKEN, CHANNEL_ID
from video_fetcher import fetch_natural_video

logger = logging.getLogger(__name__)


async def send_post_to_channel(text: str, target_channel: str = None, attach_media: bool = True, attach_video: bool = True) -> bool:
    """
    Sends the post to Telegram channel with HTML formatting.
    Supports video or photo attachment from Pinterest (Auto) or Pexels.
    """
    channel = target_channel or CHANNEL_ID

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return False

    bot = Bot(token=BOT_TOKEN)

    media_path = None
    media_type = "text"

    should_attach = attach_media and attach_video

    if should_attach:
        try:
            media_path, media_type = fetch_natural_video()
        except Exception as ve:
            logger.warning(f"Failed to fetch media, falling back to text post: {ve}")

    try:
        if media_path and os.path.exists(media_path):
            if media_type == "video":
                logger.info(f"Publishing video post to channel {channel}...")
                with open(media_path, "rb") as vf:
                    message = await bot.send_video(
                        chat_id=channel,
                        video=vf,
                        caption=text,
                        parse_mode="HTML",
                        supports_streaming=True,
                    )
            else: # photo from Pinterest
                logger.info(f"Publishing photo post to channel {channel}...")
                with open(media_path, "rb") as pf:
                    message = await bot.send_photo(
                        chat_id=channel,
                        photo=pf,
                        caption=text,
                        parse_mode="HTML",
                    )
            
            logger.info(f"Media post published successfully. Message ID: {message.message_id}")
            try:
                os.remove(media_path)
            except Exception:
                pass
            return True

        else:
            logger.info(f"Publishing text post to channel {channel}...")
            message = await bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"Text post published successfully. Message ID: {message.message_id}")
            return True

    except TelegramError as e:
        logger.error(f"Telegram API Error while posting: {e}")
        try:
            logger.info("Retrying with plain text message...")
            message = await bot.send_message(
                chat_id=channel,
                text=text,
                parse_mode=None,
                disable_web_page_preview=True,
            )
            return True
        except Exception as retry_err:
            logger.error(f"Retry failed: {retry_err}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error while sending post: {e}")
        return False
