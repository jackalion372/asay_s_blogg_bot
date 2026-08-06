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
from ai_handler import get_admin_ai_response, update_subscriber_context, SUBSCRIBERS_DB
from scheduler import setup_scheduler, WEEKLY_STATS
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

logger = logging.getLogger(__name__)


def check_is_admin(user_id: str) -> bool:
    """Checks strictly whether user_id matches the official Admin ID 8100325700."""
    return str(user_id).strip() == EXACT_ADMIN_ID


def get_subscriber_markup() -> InlineKeyboardMarkup:
    """Returns Subscriber Inline Keyboard with [📩 Adminga Murojaat] button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Adminga Murojaat", callback_data="sub_contact_admin")]
    ])


def get_admin_dashboard_markup() -> InlineKeyboardMarkup:
    """Returns Admin Dashboard Inline Keyboard with 6 professional sections."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton("✏️ Post Yaratish", callback_data="admin_create_post")
        ],
        [
            InlineKeyboardButton("📋 Hisobotlar", callback_data="admin_reports"),
            InlineKeyboardButton("👥 Obunachilar", callback_data="admin_subscribers")
        ],
        [
            InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings"),
            InlineKeyboardButton("🔄 Post Yuborish", callback_data="admin_trigger_post")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start and /admin commands."""
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = (
            f"👑 <b>Boshqaruv Paneli — Admin {user.first_name}!</b>\n\n"
            f"📌 Kanal: <code>{CHANNEL_ID}</code>\n"
            f"⏰ Reja: <b>09:00 & 21:00</b> | Juma Maxsus: <b>07:45</b>\n\n"
            f"Kerakli bo'limni tanlang yoki topshirig'ingizni yozing:"
        )
        await update.message.reply_text(welcome_text, reply_markup=get_admin_dashboard_markup(), parse_mode="HTML")
    else:
        welcome_text = (
            "<b>@asay_s_blogg kanalining rasmiy boti.</b>\n\n"
            "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
        )
        await update.message.reply_text(welcome_text, reply_markup=get_subscriber_markup(), parse_mode="HTML")


async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button clicks for Admin and Subscribers."""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    is_admin = check_is_admin(user_id)
    data = query.data

    # --- 1. SUBSCRIBER BUTTON CALLBACKS ---
    if data == "sub_contact_admin":
        context.user_data["sub_awaiting_msg"] = True
        await query.message.reply_text(
            "📩 <b>Kanal ma'muriyatiga yubormoqchi bo'lgan murojaat yoki savolingizni yozib yuboring:</b>",
            parse_mode="HTML"
        )
        return

    # --- 2. ADMIN DASHBOARD BUTTON CALLBACKS ---
    if not is_admin:
        return

    if data == "admin_stats":
        stats_text = (
            "📊 <b>Boshqaruv Statistikasi:</b>\n\n"
            f"👤 <b>Murojaat qilgan obunachilar:</b> {len(SUBSCRIBERS_DB)} ta\n"
            f"📝 <b>Bugungi chiqarilgan postlar:</b> {WEEKLY_STATS['posts_sent']} ta\n"
            f"💬 <b>Haftalik xabarlar soni:</b> {WEEKLY_STATS['messages_received']} ta\n"
            f"⚡ <b>Server holati:</b> 24/7 Bulutda Faol (Render)"
        )
        await query.message.reply_text(stats_text, reply_markup=get_admin_dashboard_markup(), parse_mode="HTML")

    elif data == "admin_create_post":
        context.user_data["admin_creating_post"] = True
        post_options_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 HD Video Bilan", callback_data="post_mode_video")],
            [InlineKeyboardButton("📝 Faqat Matn", callback_data="post_mode_text")]
        ])
        await query.message.reply_text(
            "✏️ <b>Kanalga yuboriladigan post matnini kiriting yoki media turini tanlang:</b>",
            reply_markup=post_options_keyboard,
            parse_mode="HTML"
        )

    elif data == "post_mode_video":
        context.user_data["post_with_video"] = True
        await query.message.reply_text("📹 Post matnini yuboring (HD tabiat videosi bilan joylanadi):")

    elif data == "post_mode_text":
        context.user_data["post_with_video"] = False
        await query.message.reply_text("📝 Post matnini yuboring (faqat matn joylanadi):")

    elif data == "admin_reports":
        report_text = (
            "📋 <b>Haftalik Hisobotlar Bo'limi:</b>\n\n"
            f"• <b>Oxirgi hisobot:</b> Har Yakshanba 20:00 da avtomatik yuboriladi.\n"
            f"• <b>Joriy haftada postlar:</b> {WEEKLY_STATS['posts_sent']} ta\n"
            f"• <b>Joriy haftada kelgan xabarlar:</b> {WEEKLY_STATS['messages_received']} ta\n"
            f"• <b>Manba sahihligi:</b> 100% Sahih al-Buxoriy & Muslim"
        )
        await query.message.reply_text(report_text, reply_markup=get_admin_dashboard_markup(), parse_mode="HTML")

    elif data == "admin_subscribers":
        if not SUBSCRIBERS_DB:
            sub_list_text = "👥 <b>Obunachilar Bo'limi:</b>\n\nHozircha murojaat qilgan obunachilar yo'q."
        else:
            sub_lines = []
            for uid, info in list(SUBSCRIBERS_DB.items())[-10:]:
                sub_lines.append(f"• <b>{info['name']}</b> (@{info['username']} / ID: <code>{uid}</code>) — Oxirgi xabar: {info['last_seen']}")
            sub_list_text = "👥 <b>Oxirgi Murojaat Qilgan Obunachilar:</b>\n\n" + "\n".join(sub_lines)

        await query.message.reply_text(sub_list_text, reply_markup=get_admin_dashboard_markup(), parse_mode="HTML")

    elif data == "admin_settings":
        settings_text = (
            "⚙️ <b>Tizim Sozlamalari:</b>\n\n"
            f"⏰ <b>Kunlik postlar vaqti:</b> 09:00 & 21:00 ({POST_TIMEZONE})\n"
            f"🕌 <b>Juma maxsus posti:</b> Juma 07:45\n"
            f"📊 <b>Hisobot vaqti:</b> Yakshanba 20:00\n"
            f"🤖 <b>AI Modeli:</b> Groq Llama-3.3-70B\n"
            f"🔒 <b>Admin ID:</b> <code>{EXACT_ADMIN_ID}</code>"
        )
        await query.message.reply_text(settings_text, reply_markup=get_admin_dashboard_markup(), parse_mode="HTML")

    elif data == "admin_trigger_post":
        await query.message.reply_text("⏳ Post yaratilmoqda va kanalga yuborilmoqda...")
        post_content = generate_daily_post(slot="morning")
        success = await send_post_to_channel(post_content, attach_media=True)
        if success:
            await query.message.reply_text("✅ Post kanalga muvaffaqiyatli joylashtirildi!")
        else:
            await query.message.reply_text("❌ Post yuborishda xatolik.")

    elif data.startswith("reply_user_"):
        target_user_id = data.replace("reply_user_", "")
        context.user_data["reply_target_user_id"] = target_user_id
        cancel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Aloqani Yakunlash", callback_data=f"cancel_reply_{target_user_id}")]
        ])
        await query.message.reply_text(
            "✍️ <b>Obunachiga yuboriladigan matningizni yozing:</b>",
            reply_markup=cancel_keyboard,
            parse_mode="HTML"
        )

    elif data.startswith("cancel_reply_"):
        context.user_data.pop("reply_target_user_id", None)
        await query.message.reply_text("❌ Obunachi bilan aloqa yakunlandi.")


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles private text messages:
    - If Telegram ID == 8100325700 (Admin):
        - Creating post / responding to subscriber -> delivers message.
        - 'Mijozga nima deb javob beray?' or general queries -> AI Executive Assistant.
    - If Subscriber (Other ID):
        - Sends fixed text: '@asay_s_blogg kanalining rasmiy boti. Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin.'
        - Relays message to Admin ID 8100325700 with [💬 Javob Yozish] & [❌ Yakunlash] buttons.
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

    # 1. ADMIN LOGIC (ID 8100325700)
    if is_admin:
        lower_text = user_text.lower()

        # Handle Admin creating custom post
        if context.user_data.pop("admin_creating_post", False):
            attach_v = context.user_data.pop("post_with_video", True)
            await update.message.reply_text("⏳ Yozgan matningiz kanalga joylashtirilmoqda...")
            success = await send_post_to_channel(user_text, attach_media=attach_v)
            if success:
                await update.message.reply_text("✅ Yozgan matningiz kanalga joylashtirildi!")
            else:
                await update.message.reply_text("❌ Joylashtirishda xatolik.")
            return

        # Handle session closing
        if any(phrase in lower_text for phrase in ["yozib boldim", "yozib bo'ldim", "boldi kerak emas", "bo'ldi kerak emas", "kerak emas", "bekor qilish"]):
            context.user_data.pop("reply_target_user_id", None)
            await update.message.reply_text("Obunachi bilan aloqa yakunlandi.")
            return

        # If Admin is responding to a subscriber
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
        await update.message.reply_text(ai_reply, reply_markup=get_admin_dashboard_markup())
        return

    # 2. SUBSCRIBER LOGIC (Other IDs)
    WEEKLY_STATS["messages_received"] += 1
    update_subscriber_context(user_name=user_name, username=username, user_id=user_id, text=user_text, time_str=time_str)

    # A. Send fixed text to subscriber
    subscriber_fixed_msg = (
        "@asay_s_blogg kanalining rasmiy boti.\n"
        "Bot avtomatik javob bermaydi. Xabaringizni yozib qoldirishingiz mumkin."
    )
    await update.message.reply_text(subscriber_fixed_msg, reply_markup=get_subscriber_markup())

    # B. Relay message to Admin ID 8100325700 with [💬 Javob Yozish] & [❌ Yakunlash]
    try:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 Javob Yozish", callback_data=f"reply_user_{user_id}"),
                InlineKeyboardButton("❌ Yakunlash", callback_data=f"cancel_reply_{user_id}")
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
        await update.message.reply_text(subscriber_fixed_msg, reply_markup=get_subscriber_markup())

        try:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💬 Javob Yozish", callback_data=f"reply_user_{user_id}"),
                    InlineKeyboardButton("❌ Yakunlash", callback_data=f"cancel_reply_{user_id}")
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
    application.add_handler(CommandHandler("admin", start_command))
    application.add_handler(CommandHandler("post_now", post_morning_command))

    application.add_handler(CallbackQueryHandler(handle_callback_queries))
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
