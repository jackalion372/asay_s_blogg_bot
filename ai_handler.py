import os
import logging
from openai import OpenAI
from config import GROQ_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Context memory for tracking subscribers
SUBSCRIBERS_DB = {}  # user_id -> {"name": str, "username": str, "last_seen": str, "msg_count": int}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    """Tracks unique subscribers and their latest message time."""
    if user_id not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id] = {"name": user_name, "username": username, "last_seen": time_str, "msg_count": 1}
    else:
        SUBSCRIBERS_DB[user_id]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id]["msg_count"] += 1


def get_admin_ai_response(user_prompt: str, admin_name: str) -> str:
    """
    Executive AI handler for Admin (ID: 8100325700).
    Connects to Groq Llama-3.3-70B with detailed console error logging.
    Falls back to OpenAI GPT-4o-mini if Groq fails.
    """
    clean_prompt = user_prompt.strip().lower()

    # Exact greeting match for quick test requirement
    if clean_prompt in ["salom", "assalomu alaykum", "salom alaykum"]:
        return "Va alaykum assalom, bugun qanday yordam kerak?"

    system_instruction = (
        "Sen @asay_s_blogg kanali adminining shaxsiy intellektual Sun'iy Intellekt (AI) yordamchisisisan.\n\n"
        "MULOQOT VA QOIDALAR:\n"
        "1. Admin bilan huddi ChatGPT (GPT-4) inson bilan biror vazifa yoki mavzu to'g'risida gaplashgandek to'liq, samimiy, aqlli va tabiiy muloqot qil.\n"
        "2. Admin har qanday mavzuda (vazifalar, kanal strategiyasi, post g'oyalari, islomiy va hayotiy savollar) murojaat qilsa — to'g'ridan-to'g'ri va mukammal javob ber.\n"
        "3. Hech qanday variantlar ko'rsatish, 'quyidagilardan birini tanlang' degan sun'iy cheklovlar va shablonlar ISHLATILMAYDI.\n"
        "4. Til: O'zbek tili. Javoblaring ravon, tartibli hamda foydali bo'lsin."
    )

    # 1. TRY GROQ API (Llama-3.3-70B)
    if GROQ_API_KEY:
        try:
            logger.info(f"Sending prompt to Groq API (Llama-3.3-70B)... [Prompt: {user_prompt[:30]}...]")
            client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            ai_text = response.choices[0].message.content.strip()
            logger.info(f"Groq API Response received successfully ({len(ai_text)} chars).")
            return ai_text
        except Exception as groq_err:
            logger.error(f"❌ GROQ API ERROR: {groq_err}", exc_info=True)

    # 2. FALLBACK TO OPENAI API (GPT-4o-mini)
    if OPENAI_API_KEY:
        try:
            logger.info("Falling back to OpenAI API (gpt-4o-mini)...")
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=600,
            )
            ai_text = response.choices[0].message.content.strip()
            logger.info("OpenAI API Response received successfully.")
            return ai_text
        except Exception as openai_err:
            logger.error(f"❌ OPENAI API ERROR: {openai_err}", exc_info=True)

    return "Assalomu alaykum, Admin. Groq AI tizimida vaqtinchalik ulanish xatosi yuz berdi. Iltimos qaytadan urinib ko'ring."
