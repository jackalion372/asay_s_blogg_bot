import asyncio
import logging
import os
import random
from datetime import datetime
from aiohttp import web
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, CHANNEL_ID, EXACT_ADMIN_ID, POST_TIMEZONE, validate_config
from ai_handler import update_subscriber_context, SUBSCRIBERS_DB, ask_admin_ai_copilot
from scheduler import setup_scheduler, WEEKLY_STATS
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

logger = logging.getLogger(__name__)


ADMIN_SETTINGS = {
    "preview_mode": True,
    "auto_post": True,
    "morning_time": "09:00",
    "evening_time": "21:00",
}

PENDING_PREVIEW_POST = {}
BROADCAST_DRAFT = {}


def check_is_admin(user_id: str) -> bool:
    return str(user_id).strip() == EXACT_ADMIN_ID


def get_language_selection_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_multilingual_welcome_prompt() -> str:
    return (
        "Assalamu Alaikum wa Rahmatullah wa Barakatuh! 🌙\n"
        "Official bot of @asay_s_blogg. Please select your preferred language below:\n\n"
        "Здравствуйте! 🌙\n"
        "Официальный бот канала @asay_s_blogg. Пожалуйста, выберите ваш язык ниже:\n\n"
        "Assalomu alaykum va rahmatullahi va barakatuh! 🌙\n"
        "@asay_s_blogg kanalining rasmiy boti. Iltimos, muloqot tilini quyida tanlang:"
    )


def get_admin_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📊 Statistika"), KeyboardButton("📝 Post Yaratish va Yuborish")],
        [KeyboardButton("🤖 AI Copilot (ChatGPT)"), KeyboardButton("👥 Obunachilar Ro'yxati")],
        [KeyboardButton("⚙️ Sozlamalar")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_admin_settings_inline_keyboard() -> InlineKeyboardMarkup:
    preview_status = "🟢 YONIQ (ON)" if ADMIN_SETTINGS["preview_mode"] else "🔴 O'CHIQ (OFF)"
    autopost_status = "🟢 YONIQ (ON)" if ADMIN_SETTINGS["auto_post"] else "🔴 O'CHIQ (OFF)"

    keyboard = [
        [
            InlineKeyboardButton(f"🔍 Preview Rejim: {preview_status}", callback_data="toggle_preview_mode")
        ],
        [
            InlineKeyboardButton(f"🤖 Avto-Post: {autopost_status}", callback_data="toggle_auto_post")
        ],
        [
            InlineKeyboardButton("📢 E'lon Tarqatish (Broadcast)", callback_data="admin_start_broadcast")
        ],
        [
            InlineKeyboardButton(f"⏰ Post Vaqtlari: {ADMIN_SETTINGS['morning_time']} & {ADMIN_SETTINGS['evening_time']}", callback_data="admin_set_post_times")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_settings_text() -> str:
    p_status = "🟢 YONIQ (ON)" if ADMIN_SETTINGS["preview_mode"] else "🔴 O'CHIQ (OFF)"
    a_status = "🟢 YONIQ (ON)" if ADMIN_SETTINGS["auto_post"] else "🔴 O'CHIQ (OFF)"
    return (
        "⚙️ <b>Admin Sozlamalari Paneli:</b>\n\n"
        f"🔍 <b>Post Preview Rejimi:</b> {p_status}\n"
        f"🤖 <b>Avtomatik Post Rejimi:</b> {a_status}\n"
        f"⏰ <b>Post Chiqish Vaqtlari:</b> {ADMIN_SETTINGS['morning_time']} va {ADMIN_SETTINGS['evening_time']} ({POST_TIMEZONE})\n"
        f"📢 <b>Obunachilar Soni:</b> {len(SUBSCRIBERS_DB)} ta\n"
        f"🔒 <b>Admin ID:</b> <code>{EXACT_ADMIN_ID}</code>\n\n"
        "<i>Quyidagi tugmalar orqali sozlamalarni o'zgartirishingiz mumkin:</i>"
    )


async def handle_preview_posting_or_direct(post_content: str, slot: str = "morning", attach_media: bool = True, bot_app=None):
    from telegram_poster import send_post_to_channel

    if ADMIN_SETTINGS.get("preview_mode", True):
        PENDING_PREVIEW_POST["content"] = post_content
        PENDING_PREVIEW_POST["slot"] = slot
        PENDING_PREVIEW_POST["attach_media"] = attach_media

        preview_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Kanalga Joylash", callback_data="approve_preview_post"),
                InlineKeyboardButton("🔄 Qayta Yaratish", callback_data="regenerate_preview_post")
            ],
            [
                InlineKeyboardButton("❌ Bekor Qilish", callback_data="cancel_preview_post")
            ]
        ])
        media_str = "📹 Video Bilan" if attach_media else "📝 Videosiz"
        preview_msg_text = (
            f"🔍 <b>[PREVIEW REJIM] Yangi Post Tayyorlandi ({media_str}):</b>\n\n"
            f"{post_content}\n\n"
            f"───────────────────\n"
            f"<i>Kanalga joylash uchun quyidagi tugmani bosing:</i>"
        )
        try:
            if bot_app and hasattr(bot_app, "bot"):
                await bot_app.bot.send_message(chat_id=EXACT_ADMIN_ID, text=preview_msg_text, reply_markup=preview_markup, parse_mode="HTML")
            else:
                from telegram import Bot
                async with Bot(token=BOT_TOKEN) as temp_bot:
                    await temp_bot.send_message(chat_id=EXACT_ADMIN_ID, text=preview_msg_text, reply_markup=preview_markup, parse_mode="HTML")
        except Exception as err:
            logger.error(f"Error sending preview message to admin: {err}")
    else:
        success = await send_post_to_channel(post_content, attach_media=attach_media)
        if success:
            WEEKLY_STATS["posts_sent"] += 1
            logger.info(f"Daily {slot} post published directly to channel.")


async def check_user_subscribed(bot, user_id: str) -> bool:
    """Dynamically verifies 24/7 if user is a member of CHANNEL_ID using Telegram Bot API."""
    if check_is_admin(user_id):
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logger.warning(f"Could not verify channel subscription for {user_id}: {e}")
        return True


def get_channel_subscription_prompt(lang: str) -> tuple:
    channel_clean = CHANNEL_ID.replace("@", "")
    channel_url = f"https://t.me/{channel_clean}"

    if lang == "en":
        text = (
            "⚠️ <b>Mandatory Channel Subscription Required!</b>\n\n"
            f"To use this bot and message the admin, you must be a member of our official channel: <b>{CHANNEL_ID}</b>.\n\n"
            "Please join the channel below and click <b>Verify Subscription</b>."
        )
        btn_join = "📢 Join Channel"
        btn_verify = "✅ Verify Subscription"
    elif lang == "ru":
        text = (
            "⚠️ <b>Требуется обязательная подписка на канал!</b>\n\n"
            f"Чтобы использовать бота и написать администратору, подпишитесь на наш канал: <b>{CHANNEL_ID}</b>.\n\n"
            "Пожалуйста, подпишитесь на канал ниже и нажмите <b>Проверить подписку</b>."
        )
        btn_join = "📢 Подписаться на канал"
        btn_verify = "✅ Проверить подписку"
    else:  # Default Uzbek
        text = (
            "⚠️ <b>Rasmiy Kanalga Obuna Bo'lish Shart!</b>\n\n"
            f"Botdan foydalanish va adminga murojaat yuborish uchun rasmiy kanalimizga obuna bo'lishingiz lozim: <b>{CHANNEL_ID}</b>.\n\n"
            "Iltimos, quyidagi tugma orqali kanalga a'zo bo'ling va <b>Obunani Tekshirish</b> tugmasini bosing:"
        )
        btn_join = "📢 Kanalga A'zo Bo'lish"
        btn_verify = "✅ Obunani Tekshirish"

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_join, url=channel_url)],
        [InlineKeyboardButton(btn_verify, callback_data="check_channel_sub")]
    ])
    return text, markup


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    is_admin = check_is_admin(user_id)

    if is_admin:
        welcome_text = "👑 <b>Admin Paneli — @asay_s_blogg</b>\n\nQuyidagi menyu tugmalaridan foydalanishingiz mumkin:"
        await update.message.reply_text(welcome_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")
    else:
        welcome_prompt = get_multilingual_welcome_prompt()
        await update.message.reply_text(welcome_prompt, reply_markup=get_language_selection_markup(), parse_mode="HTML")


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_prompt = get_multilingual_welcome_prompt()
    await update.message.reply_text(welcome_prompt, reply_markup=get_language_selection_markup(), parse_mode="HTML")


async def handle_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    is_admin = check_is_admin(user_id)
    data = query.data

    if data.startswith("lang_"):
        selected_lang = data.replace("lang_", "")
        context.user_data["user_lang"] = selected_lang

        # Check channel subscription dynamically
        is_subbed = await check_user_subscribed(context.bot, user_id)
        if not is_subbed:
            sub_text, sub_markup = get_channel_subscription_prompt(selected_lang)
            await query.edit_message_text(sub_text, reply_markup=sub_markup, parse_mode="HTML")
            return

        if selected_lang == "en":
            confirm_text = "✅ <b>Language set to English!</b>\n\nYou can now type and send your messages or questions directly to the channel administration anytime."
        elif selected_lang == "ru":
            confirm_text = "✅ <b>Язык установлен на Русский!</b>\n\nТеперь вы можете напрямую писать ваши сообщения администратору в любое время."
        else:
            confirm_text = "✅ <b>Muloqot tili O'zbekcha qilib tanlandi!</b>\n\nEndi kanal ma'muriyatiga o'z murojaatingizni bevosita yozishingiz mumkin."

        await query.edit_message_text(confirm_text, parse_mode="HTML")
        return

    if data == "check_channel_sub":
        lang = context.user_data.get("user_lang", "uz")
        is_subbed = await check_user_subscribed(context.bot, user_id)

        if is_subbed:
            if lang == "en":
                success_text = "✅ <b>Subscription verified!</b>\n\nYou can now type and send your messages or questions directly to the channel administration anytime."
            elif lang == "ru":
                success_text = "✅ <b>Подписка подтверждена!</b>\n\nТеперь вы можете напрямую писать ваши сообщения администратору в любое время."
            else:
                success_text = "✅ <b>Obuna tasdiqlandi!</b>\n\nEndi kanal ma'muriyatiga o'z murojaatingizni bevosita yozishingiz mumkin."
            await query.edit_message_text(success_text, parse_mode="HTML")
        else:
            if lang == "en":
                alert_text = f"❌ You have not joined {CHANNEL_ID} yet. Please join the channel first!"
            elif lang == "ru":
                alert_text = f"❌ Вы еще не подписались на {CHANNEL_ID}. Пожалуйста, сначала подпишитесь на канал!"
            else:
                alert_text = f"❌ Siz hali {CHANNEL_ID} kanaliga obuna bo'lmadingiz. Iltimos, avval kanalga a'zo bo'ling!"
            await query.answer(alert_text, show_alert=True)
        return

    if not is_admin:
        return

    if data == "toggle_preview_mode":
        ADMIN_SETTINGS["preview_mode"] = not ADMIN_SETTINGS["preview_mode"]
        status_str = "🟢 YONIQ" if ADMIN_SETTINGS["preview_mode"] else "🔴 O'CHIQ"
        await query.answer(f"Preview rejim {status_str} qilindi!", show_alert=True)
        await query.edit_message_text(get_admin_settings_text(), reply_markup=get_admin_settings_inline_keyboard(), parse_mode="HTML")
        return

    if data == "toggle_auto_post":
        ADMIN_SETTINGS["auto_post"] = not ADMIN_SETTINGS["auto_post"]
        status_str = "🟢 YONIQ" if ADMIN_SETTINGS["auto_post"] else "🔴 O'CHIQ"
        await query.answer(f"Avto-post rejim {status_str} qilindi!", show_alert=True)
        await query.edit_message_text(get_admin_settings_text(), reply_markup=get_admin_settings_inline_keyboard(), parse_mode="HTML")
        return

    if data == "approve_preview_post":
        if "content" in PENDING_PREVIEW_POST:
            content = PENDING_PREVIEW_POST.pop("content")
            await query.edit_message_text("⏳ Post kanalga joylashtirilmoqda...")
            success = await send_post_to_channel(content, attach_media=True)
            if success:
                WEEKLY_STATS["posts_sent"] += 1
                await query.edit_message_text("✅ Post kanalga muvaffaqiyatli joylashtirildi!")
            else:
                await query.edit_message_text("❌ Kanalga joylashtirishda xatolik yuz berdi.")
        else:
            await query.edit_message_text("❌ Tasdiqlanadigan post topilmadi.")
        return

    if data == "regenerate_preview_post":
        await query.edit_message_text("⏳ Yangi post generatsiya qilinmoqda...")
        new_content = generate_daily_post()
        PENDING_PREVIEW_POST["content"] = new_content
        preview_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Kanalga Joylash", callback_data="approve_preview_post"),
                InlineKeyboardButton("🔄 Qayta Yaratish", callback_data="regenerate_preview_post")
            ],
            [
                InlineKeyboardButton("❌ Bekor Qilish", callback_data="cancel_preview_post")
            ]
        ])
        preview_msg_text = (
            f"🔍 <b>[YANGILANGAN PREVIEW] Post Tayyorlandi:</b>\n\n"
            f"{new_content}\n\n"
            f"───────────────────\n"
            f"<i>Kanalga joylash uchun quyidagi tugmani bosing:</i>"
        )
        await query.edit_message_text(preview_msg_text, reply_markup=preview_markup, parse_mode="HTML")
        return

    if data == "cancel_preview_post":
        PENDING_PREVIEW_POST.clear()
        await query.edit_message_text("❌ Post bekor qilindi va o'chirildi.")
        return

    if data == "admin_start_broadcast":
        context.user_data["admin_awaiting_broadcast"] = True
        cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor Qilish", callback_data="cancel_broadcast")]])
        await query.message.reply_text(
            "📢 <b>Obunachilarga e'lon/xabar yuborish:</b>\n\nBarcha obunachilarga yubormoqchi bo'lgan xabaringizni yozib yuboring:",
            reply_markup=cancel_markup,
            parse_mode="HTML"
        )
        return

    if data == "confirm_broadcast":
        if "text" in BROADCAST_DRAFT:
            b_text = BROADCAST_DRAFT.pop("text")
            await query.edit_message_text("⏳ E'lon barcha obunachilarga tarqatilmoqda...")
            success_count = 0
            failed_count = 0
            for target_uid in list(SUBSCRIBERS_DB.keys()):
                try:
                    await context.bot.send_message(chat_id=target_uid, text=b_text)
                    success_count += 1
                except:
                    failed_count += 1
            await query.edit_message_text(f"✅ <b>E'lon tarqatildi!</b>\n👥 <b>Yuborildi:</b> {success_count} ta\n⚠️ <b>Yetib barmadi:</b> {failed_count} ta", parse_mode="HTML")
        else:
            await query.edit_message_text("❌ Tarqatiladigan e'lon topilmadi.")
        return

    if data == "cancel_broadcast":
        context.user_data.pop("admin_awaiting_broadcast", None)
        BROADCAST_DRAFT.clear()
        await query.edit_message_text("❌ E'lon yuborish bekor qilindi.")
        return

    if data == "admin_set_post_times":
        time_options = InlineKeyboardMarkup([
            [InlineKeyboardButton("08:00 & 20:00", callback_data="set_time_08_20"), InlineKeyboardButton("09:00 & 21:00", callback_data="set_time_09_21")],
            [InlineKeyboardButton("10:00 & 22:00", callback_data="set_time_10_22"), InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_settings")]
        ])
        await query.edit_message_text(f"⏰ <b>Vaqt tanlang:</b>\nHozirgi: <b>{ADMIN_SETTINGS['morning_time']}</b> & <b>{ADMIN_SETTINGS['evening_time']}</b>", reply_markup=time_options, parse_mode="HTML")
        return

    if data.startswith("set_time_"):
        pair = data.replace("set_time_", "")
        if pair == "08_20": ADMIN_SETTINGS["morning_time"], ADMIN_SETTINGS["evening_time"] = "08:00", "20:00"
        elif pair == "09_21": ADMIN_SETTINGS["morning_time"], ADMIN_SETTINGS["evening_time"] = "09:00", "21:00"
        elif pair == "10_22": ADMIN_SETTINGS["morning_time"], ADMIN_SETTINGS["evening_time"] = "10:00", "22:00"
        await query.answer("Vaqt o'zgartirildi!", show_alert=True)
        await query.edit_message_text(get_admin_settings_text(), reply_markup=get_admin_settings_inline_keyboard(), parse_mode="HTML")
        return

    if data == "hub_ai_post":
        media_options = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📹 HD Video Bilan", callback_data="ai_post_video"),
                InlineKeyboardButton("📝 Videosiz (Faqat Matn)", callback_data="ai_post_text")
            ]
        ])
        await query.edit_message_text(
            "🤖 <b>AI Post Generatsiyasi:</b>\n\nPost bilan birga HD Tabiat videosi biriktirilsinmi?",
            reply_markup=media_options,
            parse_mode="HTML"
        )
        return

    if data == "hub_manual_post":
        media_options = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📹 HD Video Bilan", callback_data="manual_post_video"),
                InlineKeyboardButton("📝 Videosiz (Faqat Matn)", callback_data="manual_post_text")
            ]
        ])
        await query.edit_message_text(
            "✍️ <b>Qo'lda Post Yozish:</b>\n\nPostingizga HD Tabiat videosi biriktirilsinmi?",
            reply_markup=media_options,
            parse_mode="HTML"
        )
        return

    if data == "ai_post_video":
        await query.edit_message_text("⏳ AI HD Video bilan post generatsiya qilmoqda...")
        post_content = generate_daily_post(slot="morning")
        await handle_preview_posting_or_direct(post_content, slot="morning", attach_media=True, bot_app=context.application)
        return

    if data == "ai_post_text":
        await query.edit_message_text("⏳ AI matnli post generatsiya qilmoqda...")
        post_content = generate_daily_post(slot="morning")
        await handle_preview_posting_or_direct(post_content, slot="morning", attach_media=False, bot_app=context.application)
        return

    if data == "manual_post_video":
        context.user_data["admin_creating_post"] = True
        context.user_data["post_with_video"] = True
        await query.edit_message_text("📹 <b>HD Video bilan joylanadigan post matnini yuboring:</b>", parse_mode="HTML")
        return

    if data == "manual_post_text":
        context.user_data["admin_creating_post"] = True
        context.user_data["post_with_video"] = False
        await query.edit_message_text("📝 <b>Faqat matnli post matnini yuboring:</b>", parse_mode="HTML")
        return

    if data == "admin_stats":
        stats_text = f"📊 <b>Statistika:</b>\n\n👤 <b>Jami obunachi:</b> {len(SUBSCRIBERS_DB)}\n📝 <b>Bugungi post:</b> {WEEKLY_STATS['posts_sent']}"
        await query.message.reply_text(stats_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")

    elif data == "admin_subscribers":
        sub_list_text = "👥 <b>Obunachilar:</b> " + (f"{len(SUBSCRIBERS_DB)} ta." if SUBSCRIBERS_DB else "Bo'sh.")
        await query.message.reply_text(sub_list_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")

    elif data == "admin_settings":
        await query.message.reply_text(get_admin_settings_text(), reply_markup=get_admin_settings_inline_keyboard(), parse_mode="HTML")

    if data == "admin_search_and_msg_user":
        context.user_data["admin_awaiting_target_input"] = True
        await query.message.reply_text(
            "🔍 <b>Obunachiga bevosita xabar yuborish:</b>\n\n"
            "Iltimos, obunachining Telegram Username (masalan <code>@username</code>) yoki ID raqamini (masalan <code>123456789</code>) yozib yuboring:",
            parse_mode="HTML"
        )
        return

    if data.startswith("reply_user_"):
        target_user_id = data.replace("reply_user_", "")
        context.user_data["reply_target_user_id"] = target_user_id
        target_info = SUBSCRIBERS_DB.get(target_user_id, {})
        target_name = target_info.get("name", "Obunachi")
        target_uname = target_info.get("username", "username_yoq")
        await query.message.reply_text(
            f"💬 <b>Obunachi tanlandi:</b> {target_name} (@{target_uname} / ID: <code>{target_user_id}</code>)\n\n"
            "Endi unga yubormoqchi bo'lgan xabaringizni yozib yuboring:",
            parse_mode="HTML"
        )
        return

    if data.startswith("cancel_reply_"):
        context.user_data.pop("reply_target_user_id", None)
        await query.message.reply_text("❌ Aloqa yakunlandi.")


async def handle_user_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return

    user_text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type != "private":
        return

    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "Foydalanuvchi"
    username = update.effective_user.username or "username_yoq"
    time_str = datetime.now().strftime("%H:%M")

    is_admin = check_is_admin(user_id)

    if is_admin:
        lower_text = user_text.lower()

        if user_text == "📊 Statistika":
            stats_text = (
                "📊 <b>Statistika Bo'limi:</b>\n\n"
                f"👤 <b>Jami obunachi soni:</b> {len(SUBSCRIBERS_DB)} ta\n"
                f"📝 <b>Bugungi postlar soni:</b> {WEEKLY_STATS['posts_sent']} ta\n"
                f"📈 <b>Haftalik murojaatlar:</b> {WEEKLY_STATS['messages_received']} ta\n"
                f"⚡ <b>Server holati:</b> 24/7 Bulutda Faol (Render)"
            )
            await update.message.reply_text(stats_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")
            return

        if user_text in ["📝 Post Yaratish va Yuborish", "🔄 Instant Post Yuborish", "✏️ Post Yaratish"]:
            context.user_data.pop("admin_ai_mode", None)
            post_hub_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🤖 AI Instant Post (Avtomatik)", callback_data="hub_ai_post")
                ],
                [
                    InlineKeyboardButton("✍️ Qo'lda Matn Yozish", callback_data="hub_manual_post")
                ]
            ])
            await update.message.reply_text(
                "📝 <b>Post Yaratish va Yuborish Bo'limi:</b>\n\n"
                "Qanday usulda post yaratmoqchisiz?",
                reply_markup=post_hub_keyboard,
                parse_mode="HTML"
            )
            return

        if user_text == "👥 Obunachilar Ro'yxati":
            if not SUBSCRIBERS_DB:
                sub_list_text = "👥 <b>Obunachilar Bo'limi:</b>\n\nHozircha ma'lumotlar bazasida obunachilar topilmadi."
                inline_sub_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Username/ID bo'yicha qidirib yozish", callback_data="admin_search_and_msg_user")]
                ])
            else:
                sub_lines = []
                keyboard_rows = []
                for uid, info in list(SUBSCRIBERS_DB.items())[-8:]:
                    uname_str = f"@{info.get('username')}" if info.get('username') != 'username_yoq' else "username yo'q"
                    sub_lines.append(f"• <b>{info['name']}</b> ({uname_str} / ID: <code>{uid}</code>) — Oxirgi: {info.get('last_seen', 'Yaqinda')}")
                    btn_label = f"💬 {info['name']} ({uname_str})"
                    keyboard_rows.append([InlineKeyboardButton(btn_label, callback_data=f"reply_user_{uid}")])

                keyboard_rows.append([InlineKeyboardButton("🔍 Username yoki ID kiritib yuborish", callback_data="admin_search_and_msg_user")])
                inline_sub_keyboard = InlineKeyboardMarkup(keyboard_rows)

                sub_list_text = (
                    f"👥 <b>Obunachilar Ro'yxati (Jami saqlanganlar: {len(SUBSCRIBERS_DB)} ta):</b>\n\n" +
                    "\n".join(sub_lines) +
                    "\n\n<i>Obunachiga xabar yuborish uchun tugmalardan foydalaning yoki username/ID orqali qidirib yozing:</i>"
                )
            await update.message.reply_text(sub_list_text, reply_markup=inline_sub_keyboard, parse_mode="HTML")
            return

        if context.user_data.pop("admin_awaiting_target_input", False):
            clean_input = user_text.replace("@", "").strip().lower()
            found_uid = None
            found_info = None

            for uid, info in SUBSCRIBERS_DB.items():
                if str(uid) == clean_input or str(info.get("username", "")).lower() == clean_input:
                    found_uid = uid
                    found_info = info
                    break

            if found_uid:
                context.user_data["reply_target_user_id"] = found_uid
                target_name = found_info.get("name", "Obunachi")
                target_uname = found_info.get("username", "username_yoq")
                await update.message.reply_text(
                    f"🎯 <b>Obunachi topildi:</b> {target_name} (@{target_uname} / ID: <code>{found_uid}</code>)\n\n"
                    f"Endi unga yubormoqchi bo'lgan xabaringizni yozib yuboring (bekor qilish uchun <i>'bekor qilish'</i> deb yozing):",
                    parse_mode="HTML"
                )
            elif user_text.isdigit():
                context.user_data["reply_target_user_id"] = user_text.strip()
                await update.message.reply_text(
                    f"🎯 <b>Foydalanuvchi ID <code>{user_text.strip()}</code> tanlandi.</b>\n\n"
                    f"Endi unga yubormoqchi bo'lgan xabaringizni yozib yuboring:",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>'{user_text}' bo'yicha obunachi topilmadi.</b>\n\n"
                    f"Iltimos, qaytadan username (masalan <code>@username</code>) yoki ID raqamini kiriting:",
                    reply_markup=get_admin_reply_keyboard(),
                    parse_mode="HTML"
                )
            return

        if user_text == "⚙️ Sozlamalar":
            await update.message.reply_text(get_admin_settings_text(), reply_markup=get_admin_settings_inline_keyboard(), parse_mode="HTML")
            return

        if user_text == "🤖 AI Copilot (ChatGPT)":
            context.user_data["admin_ai_mode"] = True
            ai_welcome_text = (
                "🤖 <b>AI Executive Copilot (ChatGPT Rejimi) Faol!</b>\n\n"
                "Men bilan xuddi ChatGPT kabi bemalol muloqot qilishingiz mumkin:\n"
                "• Dasturlash va texnik muammolarga ilg'or yechimlar olish\n"
                "• Kanal va kontent uchun strategiyalar tuzish\n"
                "• Live internetdan so'nggi yangilik va ma'lumotlarni qidirish (xabaringizda <i>'qidir'</i> yoki <i>'izla'</i> deb yozing)\n\n"
                "<i>Savolingiz yoki topshirig'ingizni yozib yuboring! (Muloqotdan chiqish uchun menyudagi boshqa biror tugmani bosing)</i>"
            )
            await update.message.reply_text(ai_welcome_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")
            return

        if user_text in ["📊 Statistika", "🔄 Instant Post Yuborish", "✏️ Post Yaratish", "👥 Obunachilar Ro'yxati", "⚙️ Sozlamalar"]:
            context.user_data.pop("admin_ai_mode", None)

        if context.user_data.get("admin_ai_mode", False):
            wait_msg = await update.message.reply_text("⏳ <i>AI javob tayyorlamoqda...</i>", parse_mode="HTML")
            history = context.user_data.get("ai_history", [])
            ai_answer = ask_admin_ai_copilot(user_query=user_text, history=history)

            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_answer})
            context.user_data["ai_history"] = history[-8:]

            try:
                await wait_msg.edit_text(ai_answer, parse_mode="HTML")
            except Exception:
                await wait_msg.edit_text(ai_answer)
            return

        if context.user_data.pop("admin_awaiting_broadcast", False):
            BROADCAST_DRAFT["text"] = user_text
            confirm_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Yuborishni Boshlash", callback_data="confirm_broadcast"),
                    InlineKeyboardButton("❌ Bekor Qilish", callback_data="cancel_broadcast")
                ]
            ])
            await update.message.reply_text(
                f"📢 <b>E'lonni barcha {len(SUBSCRIBERS_DB)} ta obunachiga yuborishni tasdiqlaysizmi?</b>\n\n"
                f"<b>Xabar matni:</b>\n{user_text}",
                reply_markup=confirm_markup,
                parse_mode="HTML"
            )
            return

        if context.user_data.pop("admin_creating_post", False):
            attach_v = context.user_data.pop("post_with_video", True)
            await update.message.reply_text("⏳ Yozgan matningiz kanalga joylashtirilmoqda...")
            success = await send_post_to_channel(user_text, attach_media=attach_v)
            if success:
                await update.message.reply_text("✅ Yozgan matningiz kanalga joylashtirildi!", reply_markup=get_admin_reply_keyboard())
            else:
                await update.message.reply_text("❌ Joylashtirishda xatolik.", reply_markup=get_admin_reply_keyboard())
            return

        if any(phrase in lower_text for phrase in ["yozib boldim", "yozib bo'ldim", "boldi kerak emas", "bo'ldi kerak emas", "kerak emas", "bekor qilish"]):
            context.user_data.pop("reply_target_user_id", None)
            context.user_data.pop("admin_awaiting_target_input", None)
            await update.message.reply_text("Obunachi bilan aloqa yakunlandi.", reply_markup=get_admin_reply_keyboard())
            return

        if "reply_target_user_id" in context.user_data:
            target_uid = context.user_data.pop("reply_target_user_id")
            try:
                msg_for_sub = f"📩 <b>Kanal ma'muriyatidan xabar:</b>\n\n{user_text}"
                await context.bot.send_message(chat_id=target_uid, text=msg_for_sub, parse_mode="HTML")
                await update.message.reply_text(f"✅ <b>Xabar obunachiga (ID: <code>{target_uid}</code>) yetkazildi!</b>", reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")
                return
            except Exception as e:
                await update.message.reply_text(f"❌ Xatolik: {e}", reply_markup=get_admin_reply_keyboard())
                return

        await update.message.reply_text("👑 <b>Admin Paneli — @asay_s_blogg</b>", reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")
        return

    WEEKLY_STATS["messages_received"] += 1
    update_subscriber_context(user_name=user_name, username=username, user_id=user_id, text=user_text, time_str=time_str)

    if "user_lang" not in context.user_data:
        welcome_prompt = get_multilingual_welcome_prompt()
        await update.message.reply_text(welcome_prompt, reply_markup=get_language_selection_markup(), parse_mode="HTML")
        return

    lang = context.user_data["user_lang"]

    # 24/7 Live Subscription Verification via Telegram Bot API
    is_subbed = await check_user_subscribed(context.bot, user_id)
    if not is_subbed:
        sub_text, sub_markup = get_channel_subscription_prompt(lang)
        await update.message.reply_text(sub_text, reply_markup=sub_markup, parse_mode="HTML")
        return

    if lang == "en":
        ack_text = "📩 <b>Your message has been sent to the admin. We will reply shortly! 🤲</b>"
    elif lang == "ru":
        ack_text = "📩 <b>Ваше сообщение отправлено администратору. Мы ответим вам в ближайшее время! 🤲</b>"
    else:
        ack_text = "📩 <b>Xabaringiz adminga yetkazildi. Tez orada javob beramiz! 🤲</b>"

    await update.message.reply_text(ack_text, parse_mode="HTML")

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
    if not update.message or not update.message.voice:
        return

    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "Foydalanuvchi"
    username = update.effective_user.username or "username_yoq"
    is_admin = check_is_admin(user_id)

    if not is_admin:
        WEEKLY_STATS["messages_received"] += 1
        update_subscriber_context(user_name=user_name, username=username, user_id=user_id, text="[Ovozli xabar yubordi]", time_str=datetime.now().strftime("%H:%M"))

        if "user_lang" not in context.user_data:
            welcome_prompt = get_multilingual_welcome_prompt()
            await update.message.reply_text(welcome_prompt, reply_markup=get_language_selection_markup(), parse_mode="HTML")
            return

        lang = context.user_data["user_lang"]

        # 24/7 Live Subscription Verification via Telegram Bot API
        is_subbed = await check_user_subscribed(context.bot, user_id)
        if not is_subbed:
            sub_text, sub_markup = get_channel_subscription_prompt(lang)
            await update.message.reply_text(sub_text, reply_markup=sub_markup, parse_mode="HTML")
            return

        if lang == "en":
            ack_text = "🎤 <b>Your voice message has been sent to the admin. 🤲</b>"
        elif lang == "ru":
            ack_text = "🎤 <b>Ваше голосовое сообщение отправлено администратору. 🤲</b>"
        else:
            ack_text = "🎤 <b>Ovozli xabaringiz adminga yetkazildi. 🤲</b>"

        await update.message.reply_text(ack_text, parse_mode="HTML")

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
    return web.Response(text="Bot is healthy and running 24/7!")


async def keep_alive_ping():
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
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init_hook)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", start_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("lang", language_command))

    application.add_handler(CallbackQueryHandler(handle_callback_queries))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_chat))

    return application


async def post_init_hook(application: Application) -> None:
    scheduler = setup_scheduler(application)
    scheduler.start()
    asyncio.create_task(keep_alive_ping())
    logger.info("APScheduler and Keep-Alive pinger started successfully.")


async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check_handler)
    app.router.add_get('/health', health_check_handler)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP Web server running on port {port}.")
