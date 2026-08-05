import asyncio
import logging
import os
import random
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

# Conversational Memory (User ID -> List of recent messages)
USER_CONVERSATION_MEMORY = {}

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
        # Reset counters for new week
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


async def chat_with_ai(user_prompt: str, user_name: str, is_admin: bool, user_id: str) -> str:
    """Generates an AI response tailored strictly to Admin vs Subscriber privacy rules with memory."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Retrieve conversational memory (last 4 turns)
    history = USER_CONVERSATION_MEMORY.get(user_id, [])
    memory_context = ""
    if history:
        memory_context = "Recent conversation memory:\n" + "\n".join(history[-4:]) + "\n"

    if is_admin:
        role_instruction = (
            f"You are talking directly to {user_name}, the official OWNER and ADMIN of the channel @asay_s_blogg. "
            "Greet them with deep respect as the Channel Owner/Admin. "
            "You can discuss channel strategies, content ideas, post timings, and give full executive assistance."
        )
        max_tokens_val = 400
    else:
        role_instruction = (
            f"You are talking to {user_name}, a subscriber of the channel @asay_s_blogg. "
            "STRICT CONCISE HUMAN RESPONSE RULES:\n"
            "1. KEEP RESPONSES SHORT, CONCISE, AND NATURAL (2 TO 4 SENTENCES MAXIMUM). NEVER WRITE LONG WALLS OF TEXT OR ESSAYS.\n"
            "2. NEVER use words like 'bot', 'AI', 'sun'iy intellekt', 'dastur', or 'avtomatlashtirilgan'.\n"
            "3. Present yourself naturally as a human representative of the @asay_s_blogg team.\n"
            "4. NEVER reveal channel internal plans, technical setup, creation dates, or admin secrets.\n"
            "5. Explain the answer clearly, warmly, and wisely, but keep it brief like a real human Telegram message."
        )
        max_tokens_val = 180

    system_instruction = (
        f"{role_instruction}\n"
        f"{memory_context}"
        "Tone rules: Be intelligent, polite, humble, warm, and wise. "
        "Answer with authentic Islamic spirituality (Tazkiyah, Sabr, Tawakkul), wisdom, and clarity. "
        "Strictly NO modern psychology jargon, NO secular self-help terms."
    )

    response_text = ""
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
                max_tokens=max_tokens_val,
            )
            response_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Chat Error: {e}")

    if not response_text and openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=max_tokens_val,
            )
            response_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    if not response_text:
        response_text = "Assalomu alaykum! Men @asay_s_blogg kanali vakiliman. Sizga qanday yordam bera olaman?"

    # Update conversation memory
    if user_id not in USER_CONVERSATION_MEMORY:
        USER_CONVERSATION_MEMORY[user_id] = []
    USER_CONVERSATION_MEMORY[user_id].append(f"User: {user_prompt}")
    USER_CONVERSATION_MEMORY[user_id].append(f"Assistant: {response_text}")

    return response_text


async def handle_admin_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks for Admin to reply to subscribers directly."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_user_"):
        target_user_id = data.replace("reply_user_", "")
        context.user_data["reply_target_user_id"] = target_user_id
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✍️ <i>Ushbu obunachiga javob yozish uchun oddiy matn yuboring:</i>",
            parse_mode="HTML"
        )


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles private messages from users, relays subscriber messages to Admin ID 8100325700 with reply button."""
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

    # Check if Admin is responding to a subscriber via active target session
    if is_admin and "reply_target_user_id" in context.user_data:
        target_uid = context.user_data.pop("reply_target_user_id")
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=f"Assalomu alaykum! Kanal ma'muriyati javobi:\n\n{user_text}"
            )
            await update.message.reply_text("✅ Javobingiz obunachiga muvaffaqiyatli yetkazildi!")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Obunachiga yuborishda xatolik: {e}")
            return

    # Relay subscriber messages directly to Admin ID 8100325700 with inline reply button
    if not is_admin:
        WEEKLY_STATS["messages_received"] += 1
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

    # Indicate typing with human delay for subscribers
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    if not is_admin:
        human_delay = random.uniform(2.2, 3.8)
        await asyncio.sleep(human_delay)

    ai_reply = await chat_with_ai(user_prompt=user_text, user_name=user_name, is_admin=is_admin, user_id=user_id)
    await update.message.reply_text(ai_reply)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Polite human handler for voice messages."""
    if not update.message or not update.message.voice:
        return
    
    user_id = str(update.effective_user.id)
    is_admin = check_is_admin(user_id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(2.0)

    if is_admin:
        await update.message.reply_text("Assalomu alaykum, Hurmatli Admin! Ovozli xabaringiz qabul qilindi.")
    else:
        await update.message.reply_text(
            "Assalomu alaykum! Ovozli xabaringiz uchun rahmat. "
            "Kanalimiz vakillari tez orada xabaringiz bilan tanishib chiqishadi."
        )


async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command /reply <user_id> <message> to reply to any subscriber."""
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
            text=f"Assalomu alaykum! Kanal ma'muriyati javobi:\n\n{reply_msg}"
        )
        await update.message.reply_text("✅ Javobingiz obunachiga muvaffaqiyatli yetkazildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = (
            f"Assalomu alaykum, Hurmatli Kanal Egasi / Admin ({user.first_name})!\n\n"
            f"🤖 Status: <b>@asay_s_blogg Professional System Active</b>\n"
            f"📌 Channel: <code>{CHANNEL_ID}</code>\n"
            f"⏰ Schedule:\n"
            f"  • Kunlik postlar: <b>09:00 & 21:00</b> ({POST_TIMEZONE})\n"
            f"  • Juma Maxsus: <b>Juma 08:00</b>\n"
            f"  • Haftalik Hisobot: <b>Yakshanba 20:00</b>\n\n"
            f"💬 Men sizning o'qilona yordamchingizman. Xohlagan savolingizni berishingiz mumkin.\n"
            f"📩 Obunachilar yozgan xabarlar tugma bilan birga avtomatik sizga yetkaziladi!"
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

    logger.info(f"Bot starting with All 6 Professional Features & Admin ID {EXACT_ADMIN_ID}...")
    application.run_polling()


if __name__ == "__main__":
    main()
