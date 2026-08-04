import asyncio
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
    ADMIN_USER_ID,
    POST_TIMEZONE,
    validate_config,
)
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def trigger_posting(slot: str = "morning"):
    """Scheduled task function that creates and publishes a post for a specific slot ('morning' or 'evening')."""
    logger.info(f"Executing scheduled task ({slot}): Generating post...")
    try:
        post_content = generate_daily_post(slot=slot)
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            logger.info(f"Daily {slot} post successfully created and published.")
        else:
            logger.error(f"Failed to publish {slot} post to channel.")
    except Exception as e:
        logger.error(f"Error during scheduled {slot} post generation/posting: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    welcome_text = (
        f"Assalomu alaykum, {user.first_name}!\n\n"
        f"🤖 Bot active: <b>@asay_s_blogg Telegram Automation System</b>\n\n"
        f"📌 Channel: <code>{CHANNEL_ID}</code>\n"
        f"⏰ Schedule:\n"
        f"  • Ertalabki post: <b>09:00</b> ({POST_TIMEZONE})\n"
        f"  • Kechki post: <b>21:00</b> ({POST_TIMEZONE})\n\n"
        f"📅 Kunlar tartibi:\n"
        f"  • <b>Toq kunlar (Dush, Chor, Jum, Yak)</b>: Sof Islomiy Ma'rifat\n"
        f"  • <b>Juft kunlar (Ses, Pay, Shan)</b>: Insoniy samimiyat, Quvonch & Sokinlik\n\n"
        f"Commands:\n"
        f"/post_morning — Test morning post immediately\n"
        f"/post_evening — Test evening post immediately"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def post_morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /post_morning admin command."""
    await update.message.reply_text("⏳ Ertalabki post yaratilmoqda...")
    try:
        post_content = generate_daily_post(slot="morning")
        await update.message.reply_text(f"📝 <b>Ertalabki Post:</b>\n\n{post_content}", parse_mode="HTML")
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            await update.message.reply_text("✅ Ertalabki post kanalga muvaffaqiyatli joylashtirildi!")
        else:
            await update.message.reply_text("❌ Kanalga yuborishda xatolik.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


async def post_evening_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /post_evening admin command."""
    await update.message.reply_text("⏳ Kechki post yaratilmoqda...")
    try:
        post_content = generate_daily_post(slot="evening")
        await update.message.reply_text(f"📝 <b>Kechki Post:</b>\n\n{post_content}", parse_mode="HTML")
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            await update.message.reply_text("✅ Kechki post kanalga muvaffaqiyatli joylashtirildi!")
        else:
            await update.message.reply_text("❌ Kanalga yuborishda xatolik.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """Sets up APScheduler for 2 daily posts: Morning (09:00) and Evening (21:00)."""
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

    logger.info(f"Scheduler configured for 2 daily posts: 09:00 & 21:00 ({POST_TIMEZONE}).")
    return scheduler


async def post_init(application: Application) -> None:
    """Post initialization hook to start APScheduler inside the active asyncio loop."""
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("APScheduler started successfully inside running event loop.")


def main():
    """Main application launcher."""
    missing = validate_config()
    if missing:
        logger.warning(f"Missing config variables: {', '.join(missing)}")

    if not BOT_TOKEN:
        logger.error("Cannot start bot without BOT_TOKEN.")
        return

    # Initialize Telegram Application with post_init hook
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Add Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("post_now", post_morning_command))
    application.add_handler(CommandHandler("post_morning", post_morning_command))
    application.add_handler(CommandHandler("post_evening", post_evening_command))

    logger.info("Bot starting with 2-post daily schedule... Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
