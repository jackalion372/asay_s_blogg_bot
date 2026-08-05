import asyncio
import logging
import os
import random
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web
import requests
from openai import OpenAI

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

# Strict Admin Telegram ID
EXACT_ADMIN_ID = "8100325700"


def check_is_admin(user_id: str) -> bool:
    """Checks strictly whether user_id matches the official Admin ID '8100325700'."""
    uid = str(user_id).strip()
    configured = (ADMIN_USER_ID or os.getenv("ADMIN_USER_ID", "")).strip()
    return uid == EXACT_ADMIN_ID or uid == configured


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


async def health_check_handler(request):
    """HTTP Health Check endpoint for Render web service."""
    return web.Response(text="Bot is healthy and running 24/7!")


async def keep_alive_ping():
    """Background task to self-ping Render web service to prevent free-tier sleeping."""
    render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if not render_url:
        render_url = "https://asay-s-blogg-bot.onrender.com"

    while True:
        await asyncio.sleep(600)  # Ping every 10 minutes
        try:
            logger.info(f"Pinging web server to stay awake: {render_url}")
            requests.get(render_url, timeout=10)
        except Exception as e:
            logger.debug(f"Self ping quiet note: {e}")


async def chat_with_ai(user_prompt: str, user_name: str, is_admin: bool) -> str:
    """Generates an AI response tailored strictly to Admin vs Subscriber privacy rules."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if is_admin:
        role_instruction = (
            f"You are talking directly to {user_name}, the official OWNER and ADMIN of the channel @asay_s_blogg. "
            "Greet them with deep respect as the Channel Owner/Admin. "
            "You can discuss channel strategies, content ideas, post timings, and give full executive assistance."
        )
    else:
        role_instruction = (
            f"You are talking to {user_name}, a subscriber of the channel @asay_s_blogg. "
            "STRICT HUMAN PERCEPTION RULES:\n"
            "1. NEVER use words like 'bot', 'AI', 'sun'iy intellekt', 'dastur', or 'avtomatlashtirilgan'.\n"
            "2. Present yourself naturally as a human representative of the @asay_s_blogg team.\n"
            "3. Greet them warmly and naturally: 'Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. Sizga qanday yordam bera olaman?'\n"
            "4. NEVER reveal channel internal plans, technical setup, creation dates, or admin secrets.\n"
            "5. Be humble, quiet, polite, warm, and helpful. Answer their questions naturally in whatever language they ask."
        )

    system_instruction = (
        f"{role_instruction}\n"
        "Tone rules: Be intelligent, polite, humble, warm, and wise. "
        "Answer with authentic Islamic spirituality (Tazkiyah, Sabr, Tawakkul), wisdom, and clarity. "
        "Strictly NO modern psychology jargon, NO secular self-help terms."
    )

    if groq_key:
        try:
            client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Chat Error: {e}")

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    return "Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. Sizga qanday yordam bera olaman?"


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles private messages from users, relays subscriber messages to Admin ID 8100325700."""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type != "private":
        return

    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "Foydalanuvchi"
    username = update.effective_user.username or "username_yoq"

    is_admin = check_is_admin(user_id)

    # Relay subscriber messages directly to Admin ID 8100325700
    if not is_admin:
        try:
            admin_notification = (
                f"📩 <b>Obunachidan yangi xabar:</b>\n"
                f"👤 <b>Kimdan:</b> {user_name} (@{username} / ID: <code>{user_id}</code>)\n"
                f"💬 <b>Xabar:</b> {user_text}"
            )
            await context.bot.send_message(
                chat_id=EXACT_ADMIN_ID,
                text=admin_notification,
                parse_mode="HTML"
            )
        except Exception as notify_err:
            logger.warning(f"Could not relay message to admin {EXACT_ADMIN_ID}: {notify_err}")

    # Indicate typing with human delay for subscribers to feel 100% natural
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    if not is_admin:
        human_delay = random.uniform(2.5, 4.2)
        await asyncio.sleep(human_delay)

    ai_reply = await chat_with_ai(user_prompt=user_text, user_name=user_name, is_admin=is_admin)
    await update.message.reply_text(ai_reply)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = (
            f"Assalomu alaykum, Hurmatli Kanal Egasi / Admin ({user.first_name})!\n\n"
            f"🤖 Status: <b>@asay_s_blogg Automation System Active</b>\n"
            f"📌 Channel: <code>{CHANNEL_ID}</code>\n"
            f"⏰ Schedule:\n"
            f"  • Ertalabki post: <b>09:00</b> ({POST_TIMEZONE})\n"
            f"  • Kechki post: <b>21:00</b> ({POST_TIMEZONE})\n\n"
            f"💬 Men sizning o'qilona yordamchingizman. Xohlagan savolingizni berishingiz mumkin.\n"
            f"📩 Obunachilar yozgan barcha xabarlar avtomatik sizga yetkazib turiladi!"
        )
    else:
        welcome_text = (
            f"Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. "
            f"Sizga qanday yordam bera olaman?"
        )

    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def post_morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /post_morning admin command."""
    user_id = str(update.effective_user.id)
    if not check_is_admin(user_id):
        await update.message.reply_text("Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. Sizga qanday yordam bera olaman?")
        return

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
    user_id = str(update.effective_user.id)
    if not check_is_admin(user_id):
        await update.message.reply_text("Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. Sizga qanday yordam bera olaman?")
        return

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
    """Post initialization hook to start APScheduler & Keep-Alive pinger inside running loop."""
    scheduler = setup_scheduler()
    scheduler.start()
    asyncio.create_task(keep_alive_ping())
    logger.info("APScheduler and Keep-Alive pinger started successfully.")


async def start_web_server():
    """Starts a lightweight HTTP web server for Render PORT binding."""
    app = web.Application()
    app.router.add_get('/', health_check_handler)
    app.router.add_get('/health', health_check_handler)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP Web server running on port {port}.")


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

    # Add Interactive AI Chat Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_chat))

    # Start HTTP web server in background before Telegram polling
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())

    logger.info(f"Bot starting with Human Perception Engine & Admin ID {EXACT_ADMIN_ID}...")
    application.run_polling()


if __name__ == "__main__":
    main()
