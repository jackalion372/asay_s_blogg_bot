import asyncio
import logging
import os
import random
from datetime import datetime
from aiohttp import web
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, CHANNEL_ID, EXACT_ADMIN_ID, POST_TIMEZONE, validate_config
from ai_handler import get_admin_ai_response, update_subscriber_context
from scheduler import setup_scheduler, WEEKLY_STATS
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

logger = logging.getLogger(__name__)


def check_is_admin(user_id: str) -> bool:
    """Checks strictly whether user_id matches the official Admin ID 8100325700."""
    return str(user_id).strip() == EXACT_ADMIN_ID


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = (
            f"👑 <b>O'ng Qo'lingiz va Menejeringiz faol, Admin {user.first_name}!</b>\n\n"
            f"📌 Channel: <code>{CHANNEL_ID}</code>\n"
            f"⏰ Postlar: <b>09:00 & 21:00</b> | Juma Maxsus: <b>07:45</b>\n\n"
            f"Menga istalgan topshirig'ingizni yozishingiz mumkin."
        )
    else:
        welcome_text = (
            "<b>@asay_s_blogg kanalining rasmiy boti.</b>\n\n"
            "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
        )

    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def handle_admin_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline buttons: [💬 Obunachiga Javob Yozish] and [❌ Aloqani Yakunlash]."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_user_"):
        target_user_id = data.replace("reply_user_", "")
        context.user_data["reply_target_user_id"] = target_user_id

        cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Aloqani Yakunlash", callback_data=f"cancel_reply_{target_user_id}")]
        ])

        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✍️ <i>Obunachiga yuboriladigan matningizni yozing:</i>",
            reply_markup=cancel_keyboard,
            parse_mode="HTML"
        )
    elif data.startswith("cancel_reply_"):
        context.user_data.pop("reply_target_user_id", None)
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <i>Obunachi bilan aloqa yakunlandi.</i>",
            parse_mode="HTML"
        )


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles private text messages:
    - If Telegram ID == 8100325700 (Admin):
        - Handles 'bo'ldi kerak emas' / 'yozib bo'ldim' -> cancels reply session quietly.
        - Delivers text directly to subscriber if in active session -> '✅ Yuborildi. Aloqa yakunlandi.'
        - Handles 'Mijozga nima deb javob beray?' or general queries -> AI Executive Assistant response.
    - If Subscriber (Other ID):
        - Sends fixed text: '@asay_s_blogg kanalining rasmiy boti. Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin.'
        - Relays message to Admin ID 8100325700 with [💬 Obunachiga Javob Yozish] & [❌ Aloqani Yakunlash] buttons.
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
    time_str = datetime.now().strftime("%H:%M")

    is_admin = check_is_admin(user_id)

    # 1. ADMIN (ID 8100325700) LOGIC
    if is_admin:
        lower_text = user_text.lower()

        # Handle dismissal / session closing phrases
        if any(phrase in lower_text for phrase in ["yozib boldim", "yozib bo'ldim", "boldi kerak emas", "bo'ldi kerak emas", "kerak emas", "bekor qilish"]):
            context.user_data.pop("reply_target_user_id", None)
            await update.message.reply_text("Obunachi bilan aloqa yakunlandi.")
            return

        # If Admin is replying directly to a subscriber
        if "reply_target_user_id" in context.user_data:
            target_uid = context.user_data.pop("reply_target_user_id")
            try:
                await context.bot.send_message(chat_id=target_uid, text=user_text)
                await update.message.reply_text("✅ Yuborildi. Aloqa yakunlandi.")
                return
            except Exception as e:
                await update.message.reply_text(f"❌ Xatolik: {e}")
                return

        # AI Executive Assistant for Admin
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        ai_reply = get_admin_ai_response(user_prompt=user_text, admin_name=user_name)
        await update.message.reply_text(ai_reply)
        return

    # 2. SUBSCRIBER (OTHER ID) LOGIC
    WEEKLY_STATS["messages_received"] += 1
    update_subscriber_context(user_name=user_name, username=username, user_id=user_id, text=user_text, time_str=time_str)

    # A. Send fixed text to subscriber
    subscriber_fixed_msg = (
        "@asay_s_blogg kanalining rasmiy boti.\n"
        "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
    )
    await update.message.reply_text(subscriber_fixed_msg)

    # B. Relay message to Admin ID 8100325700 with [💬 Obunachiga Javob Yozish] & [❌ Aloqani Yakunlash]
    try:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 Obunachiga Javob Yozish", callback_data=f"reply_user_{user_id}"),
                InlineKeyboardButton("❌ Aloqani Yakunlash", callback_data=f"cancel_reply_{user_id}")
            ]
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
        update_subscriber_context(user_name=user_name, username=username, user_id=user_id, text="[Ovozli xabar yubordi]", time_str=datetime.now().strftime("%H:%M"))

        subscriber_fixed_msg = (
            "@asay_s_blogg kanalining rasmiy boti.\n"
            "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
        )
        await update.message.reply_text(subscriber_fixed_msg)

        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💬 Obunachiga Javob Yozish", callback_data=f"reply_user_{user_id}"),
                    InlineKeyboardButton("❌ Aloqani Yakunlash", callback_data=f"cancel_reply_{user_id}")
                ]
            ])
            admin_notification = (
                f"🎤 <b>Obunachidan OVOZLI XABAR:</b>\n"
                f"👤 <b>Kimdan:</b> {user_name} (@{username} / ID: <code>{user_id}</code>)"
            )
            await context.bot.send_message(chat_id=EXACT_ADMIN_ID, text=admin_notification, reply_markup=keyboard, parse_mode="HTML")
            await context.bot.forward_message(chat_id=EXACT_ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as notify_err:
            logger.warning(f"Could not relay voice to admin: {notify_err}")
    else:
        await update.message.reply_text("Ovozli xabar qabul qilindi.")


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


async def health_check_handler(request):
    """HTTP Health Check endpoint for Render web service."""
    return web.Response(text="Bot is healthy and running 24/7!")


async def keep_alive_ping():
    """Background task to self-ping Render web service to prevent free-tier sleeping."""
    render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if not render_url:
        render_url = "https://asay-s-blogg-bot.onrender.com"

    while True:
        await asyncio.sleep(600)
        try:
            requests.get(render_url, timeout=10)
        except Exception as e:
            logger.debug(f"Self ping note: {e}")


def build_application() -> Application:
    """Builds and configures Telegram application handlers."""
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init_hook)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("post_now", post_morning_command))
    application.add_handler(CommandHandler("post_morning", post_morning_command))
    application.add_handler(CommandHandler("post_evening", post_morning_command))

    application.add_handler(CallbackQueryHandler(handle_admin_reply_button))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_chat))

    return application


async def post_init_hook(application: Application) -> None:
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
