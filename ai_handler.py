import os
import logging
from openai import OpenAI
from config import GROQ_API_KEY, OPENAI_API_KEY, EXACT_ADMIN_ID

logger = logging.getLogger(__name__)

# Context memory for the last subscriber message
LAST_SUBSCRIBER_CONTEXT = {
    "user_name": "",
    "username": "",
    "user_id": "",
    "text": "",
    "time": ""
}

SUBSCRIBERS_DB = {}  # user_id -> {"name": str, "username": str, "last_seen": str, "msg_count": int}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    """Updates context memory with the latest subscriber message."""
    LAST_SUBSCRIBER_CONTEXT["user_name"] = user_name
    LAST_SUBSCRIBER_CONTEXT["username"] = username
    LAST_SUBSCRIBER_CONTEXT["user_id"] = user_id
    LAST_SUBSCRIBER_CONTEXT["text"] = text
    LAST_SUBSCRIBER_CONTEXT["time"] = time_str

    if user_id not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id] = {"name": user_name, "username": username, "last_seen": time_str, "msg_count": 1}
    else:
        SUBSCRIBERS_DB[user_id]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id]["msg_count"] += 1


def get_admin_ai_response(user_prompt: str, admin_name: str) -> str:
    """
    Pure ChatGPT-style conversational AI exclusively for Admin ID 8100325700.
    Talks naturally and intelligently about any topic/task, just like ChatGPT.
    ZERO reply options or robotic constraints.
    """
    system_instruction = (
        "Sen @asay_s_blogg kanali adminining shaxsiy intellektual Sun'iy Intellekt (AI) yordamchisisisan.\n\n"
        "MULOQOT VA QOIDALAR:\n"
        "1. Admin bilan huddi ChatGPT (GPT-4) inson bilan biror vazifa yoki mavzu to'g'risida gaplashgandek to'liq, samimiy, aqlli va tabiiy muloqot qil.\n"
        "2. Admin har qanday mavzuda (vazifalar, kanal strategiyasi, post g'oyalari, islomiy va hayotiy savollar) murojaat qilsa — to'g'ridan-to'g'ri va mukammal javob ber.\n"
        "3. Hech qanday variantlar ko'rsatish, 'quyidagilardan birini tanlang' degan sun'iy cheklovlar va shablonlar ISHLATILMAYDI.\n"
        "4. Til: O'zbek tili. Javoblaring ravon, tartibli hamda foydali bo'lsin."
    )

    if GROQ_API_KEY:
        try:
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
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Chat Error: {e}")

    if OPENAI_API_KEY:
        try:
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
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    return "Tushundim, Admin."
