import asyncio
import logging
import os
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
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

# Memory for last subscriber interaction so Admin never has to explain which user or text
LAST_SUBSCRIBER_CONTEXT = {
    "user_name": "",
    "username": "",
    "user_id": "",
    "text": "",
    "time": ""
}

# Weekly interaction counter
WEEKLY_STATS = {"posts_sent": 0, "messages_received": 0}


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
            WEEKLY_STATS["posts_sent"] += 1
            logger.info(f"Daily {slot} post successfully created and published.")
        else:
            logger.error(f"Failed to publish {slot} post to channel.")
    except Exception as e:
        logger.error(f"Error during scheduled {slot} post generation/posting: {e}")


async def trigger_friday_special():
    """Special Friday Mubarak post at 08:00 AM every Friday."""
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
            logger.info("Friday Mubarak special post published.")
    except Exception as e:
        logger.error(f"Error publishing Friday special post: {e}")


async def send_weekly_admin_summary(context: ContextTypes.DEFAULT_TYPE):
    """Sends weekly stats summary to Admin every Sunday evening at 20:00."""
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


async def chat_with_admin_ai(user_prompt: str, user_name: str) -> str:
    """Generates executive assistance AI response exclusively for the Admin, knowing the latest subscriber message context."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    subscriber_info = ""
    if LAST_SUBSCRIBER_CONTEXT["text"]:
        subscriber_info = (
            f"LATEST SUBSCRIBER MESSAGE CONTEXT:\n"
            f"- Subscriber Name: {LAST_SUBSCRIBER_CONTEXT['user_name']} (@{LAST_SUBSCRIBER_CONTEXT['username']})\n"
            f"- Message Text: \"{LAST_SUBSCRIBER_CONTEXT['text']}\"\n"
            f"Note: You ALREADY know this message context. NEVER ask the admin 'which user?' or 'what did they write?'. "
            f"If Admin asks how to reply, hesitates, or asks for advice, IMMEDIATELY offer 2-3 smart, executive, polite Uzbek reply options tailored to this message.\n"
        )

    system_instruction = (
        f"You are the executive RIGHT-HAND MANAGER and ASSISTANT for {user_name}, the OWNER and ADMIN of @asay_s_blogg channel.\n"
        f"{subscriber_info}\n"
        "Your role: Help the admin draft replies, brainstorm high-value post ideas, analyze strategy, and format quotes/hadiths.\n"
        "STRICT STYLE RULES: Never repeat repetitive greetings ('Assalomu alaykum') constantly. Speak directly, clearly, intelligently, and productively in Uzbek.\n"
        "Strictly NO modern psychology jargon, NO secular self-help terms. Always maintain authentic Islamic dignity."
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
                max_tokens=650,
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
                max_tokens=650,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    return "Tushundim, Admin. Qanday yordam beray?"


async def handle_admin_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks for Admin to reply to subscribers directly."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_user_"):
        target_user_id = data.replace("reply_user_", "")
        context.user_data["reply_target_user_id"] = target_user_id
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✍️ <i>Javob matningizni yuboring:</i>",
            parse_mode="HTML"
        )


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles private messages:
    - If Admin: AI acts as Executive Right-Hand Manager, remembering the latest subscriber context.
    - If Subscriber: Remembers message context and relays to Admin without any auto-bot text.
    """
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

    # If ADMIN is responding to a subscriber via reply session -> send exact text with ZERO prefixes!
    if is_admin and "reply_target_user_id" in context.user_data:
        target_uid = context.user_data.pop("reply_target_user_id")
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=user_text
            )
            await update.message.reply_text("✅ Yuborildi.")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")
            return

    # FOR SUBSCRIBERS: Remember context & relay to Admin ID 8100325700. Zero auto-AI reply.
    if not is_admin:
        WEEKLY_STATS["messages_received"] += 1

        # Save into Admin Memory automatically
        LAST_SUBSCRIBER_CONTEXT["user_name"] = user_name
        LAST_SUBSCRIBER_CONTEXT["username"] = username
        LAST_SUBSCRIBER_CONTEXT["user_id"] = user_id
        LAST_SUBSCRIBER_CONTEXT["text"] = user_text
        LAST_SUBSCRIBER_CONTEXT["time"] = datetime.now().strftime("%H:%M")

        try:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Obunachiga Javob Yozish", callback_data=f"reply_user_{user_id}")]
            ])
            admin_notification = (
                f"📩 <b>Obunachidan yangi xabar:</b>\n"
                f"👤 <b>Kimdan:</b> {user_name} (@{username} / ID: <code>{user_id}</code>)\n"
                f"💬 <b>Xabar:</b> {user_text}"
            )
            await context.bot.send_message(
                chat_id=EXACT_ADMIN_ID,
                text=admin_notification,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as notify_err:
            logger.warning(f"Could not relay message to admin {EXACT_ADMIN_ID}: {notify_err}")

        # Completely silent receipt
        return

    # FOR ADMIN (Siz): AI acts as Executive Right-Hand Manager (already knows last subscriber context!)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ai_reply = await chat_with_admin_ai(user_prompt=user_text, user_name=user_name)
    await update.message.reply_text(ai_reply)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice message handler."""
    if not update.message or not update.message.voice:
        return
    
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "Foydalanuvchi"
    username = update.effective_user.username or "username_yoq"
    is_admin = check_is_admin(user_id)

    if not is_admin:
        WEEKLY_STATS["messages_received"] += 1
        LAST_SUBSCRIBER_CONTEXT["user_name"] = user_name
        LAST_SUBSCRIBER_CONTEXT["username"] = username
        LAST_SUBSCRIBER_CONTEXT["user_id"] = user_id
        LAST_SUBSCRIBER_CONTEXT["text"] = "[Ovozli xabar yubordi]"
        LAST_SUBSCRIBER_CONTEXT["time"] = datetime.now().strftime("%H:%M")

        try:
            admin_notification = (
                f"🎤 <b>Obunachidan OVOZLI XABAR:</b>\n"
                f"👤 <b>Kimdan:</b> {user_name} (@{username} / ID: <code>{user_id}</code>)"
            )
            await context.bot.send_message(chat_id=EXACT_ADMIN_ID, text=admin_notification, parse_mode="HTML")
            await context.bot.forward_message(chat_id=EXACT_ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as notify_err:
            logger.warning(f"Could not relay voice to admin: {notify_err}")
        return
    else:
        await update.message.reply_text("Ovozli xabaringiz qabul qilindi, Admin.")


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command /reply <user_id> <message> to reply directly without prefixes."""
    user_id = str(update.effective_user.id)
    if not check_is_admin(user_id):
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Foydalanish: <code>/reply <user_id> <matn></code>", parse_mode="HTML")
        return

    target_uid = args[0]
    reply_msg = " ".join(args[1:])

    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=reply_msg
        )
        await update.message.reply_text("✅ Yuborildi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = (
            f"👑 <b>O'ng Qo'lingiz va Menejeringiz faol, Admin {user.first_name}!</b>\n\n"
            f"📌 Channel: <code>{CHANNEL_ID}</code>\n"
            f"⏰ Postlar: <b>09:00 & 21:00</b> | Juma Maxsus: <b>08:00</b>\n\n"
            f"Menga istalgan savolingiz yoki kontent topshirig'ingizni yuborishingiz mumkin.\n"
            f"💡 Obunachi yozganda: 'Bunga nima deb javob bera olay?' desangiz, darhol 2-3 ta tayyor variant beraman!"
        )
    else:
        welcome_text = (
            "<b>@asay_s_blogg kanalining rasmiy boti.</b>\n\n"
            "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
        )

    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def post_morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /post_morning admin command."""
    user_id = str(update.effective_user.id)
    if not check_is_admin(user_id):
        return

    await update.message.reply_text("⏳ Post yaratilmoqda...")
    try:
        post_content = generate_daily_post(slot="morning")
        await update.message.reply_text(f"📝 <b>Post:</b>\n\n{post_content}", parse_mode="HTML")
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            await update.message.reply_text("✅ Post kanalga muvaffaqiyatli joylashtirildi!")
        else:
            await update.message.reply_text("❌ Kanalga yuborishda xatolik.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


def setup_scheduler(app_instance: Application) -> AsyncIOScheduler:
    """Sets up APScheduler for daily posts, Friday special, and Sunday admin report."""
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(POST_TIMEZONE))

    # Daily Morning & Evening posts
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

    # Friday Mubarak Special Post (Every Friday at 08:00 AM)
    scheduler.add_job(
        trigger_friday_special,
        trigger="cron",
        day_of_week="fri",
        hour=8,
        minute=0,
        name="friday_mubarak_special",
    )

    # Weekly Admin Summary (Every Sunday at 20:00 PM)
    scheduler.add_job(
        send_weekly_admin_summary,
        trigger="cron",
        day_of_week="sun",
        hour=20,
        minute=0,
        kwargs={"context": ContextTypes.DEFAULT_TYPE(app_instance)},
        name="weekly_admin_summary",
    )

    logger.info(f"Scheduler configured: 2 daily posts, Friday Special, and Sunday Admin Summary ({POST_TIMEZONE}).")
    return scheduler


async def post_init(application: Application) -> None:
    """Post initialization hook to start APScheduler & Keep-Alive pinger inside running loop."""
    scheduler = setup_scheduler(application)
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
    application.add_handler(CommandHandler("post_evening", post_morning_command))
    application.add_handler(CommandHandler("reply", reply_command))

    # Callback Query Handler for Admin Reply Button
    application.add_handler(CallbackQueryHandler(handle_admin_reply_button))

    # Voice Message Handler
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    # Interactive Text Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_chat))

    # Start HTTP web server in background before Telegram polling
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())

    logger.info(f"Bot starting with Subscriber Context Memory for Admin...")
    application.run_polling()


if __name__ == "__main__":
    main()
