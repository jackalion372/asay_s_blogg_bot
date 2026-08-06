import logging
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, ContextTypes

from config import POST_TIMEZONE, CHANNEL_ID, EXACT_ADMIN_ID
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

logger = logging.getLogger(__name__)

WEEKLY_STATS = {"posts_sent": 0, "messages_received": 0}


async def trigger_posting(slot: str = "morning"):
    logger.info(f"Executing scheduled task ({slot}): Generating post...")
    try:
        post_content = generate_daily_post(slot=slot)
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            WEEKLY_STATS["posts_sent"] += 1
            logger.info(f"Daily {slot} post published successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled post generation: {e}")


async def trigger_friday_special():
    logger.info("Executing Friday Mubarak special post...")
    friday_html = (
        "<b>Juma Ayyomingiz Muborak Bo'lsin! ✨</b>\n\n"
        "<blockquote>قال رسول الله ﷺ:\n"
        "«أَكْثِرُوا عَلَيَّ مِنَ الصَّلاَةِ فِي يَوْمِ الْجُمُعَةِ وَلَيْلَةِ الْجُمُعَةِ فَمَنْ صَلَّى عَلَيَّ صَلاَةً صَلَّى اللَّهُ عَلَيْهِ عَشْرًا»\n\n"
        "\"Send abundant blessings upon me on Friday and Friday night, for whoever sends one blessing upon me, Allah sends ten blessings upon him.\"\n\n"
        "<b>[Sunan al-Bayhaqi #5790, Sahih]</b></blockquote>\n\n"
        "<i>May your Friday be filled with light, peace, and acceptance of prayers.</i>"
    )
    try:
        success = await send_post_to_channel(friday_html, attach_media=True)
        if success:
            WEEKLY_STATS["posts_sent"] += 1
    except Exception as e:
        logger.error(f"Error publishing Friday special post: {e}")


async def send_weekly_admin_summary(context: ContextTypes.DEFAULT_TYPE):
    summary_text = (
        f"📊 <b>Haftalik Boshqaruv Hisoboti:</b>\n\n"
        f"📌 <b>Kanal:</b> <code>{CHANNEL_ID}</code>\n"
        f"📝 <b>Chiqarilgan postlar:</b> {WEEKLY_STATS['posts_sent']} ta\n"
        f"💬 <b>Obunachilar murojaati:</b> {WEEKLY_STATS['messages_received']} ta\n\n"
        f"✅ Bot 24/7 bulutda barqaror va xavfsiz ishlamoqda."
    )
    try:
        await context.bot.send_message(chat_id=EXACT_ADMIN_ID, text=summary_text, parse_mode="HTML")
        WEEKLY_STATS["posts_sent"] = 0
        WEEKLY_STATS["messages_received"] = 0
    except Exception as e:
        logger.error(f"Error sending weekly admin summary: {e}")


def setup_scheduler(app_instance: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(POST_TIMEZONE))

    scheduler.add_job(
        trigger_posting,
        trigger="cron",
        hour=9,
        minute=0,
        kwargs={"slot": "morning"},
        name="daily_morning_post",
    )

    scheduler.add_job(
        trigger_posting,
        trigger="cron",
        hour=21,
        minute=0,
        kwargs={"slot": "evening"},
        name="daily_evening_post",
    )

    scheduler.add_job(
        trigger_friday_special,
        trigger="cron",
        day_of_week="fri",
        hour=7,
        minute=45,
        name="friday_mubarak_special",
    )

    scheduler.add_job(
        send_weekly_admin_summary,
        trigger="cron",
        day_of_week="sun",
        hour=20,
        minute=0,
        kwargs={"context": ContextTypes.DEFAULT_TYPE(app_instance)},
        name="weekly_admin_summary",
    )

    return scheduler
