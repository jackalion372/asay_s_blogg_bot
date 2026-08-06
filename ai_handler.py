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
    Executive Assistant AI exclusively for Admin ID 8100325700.
    Uses Groq Llama-3.3-70B with exact specified system prompt.
    """
    subscriber_info = ""
    if LAST_SUBSCRIBER_CONTEXT["text"]:
        subscriber_info = (
            f"LATEST SUBSCRIBER MESSAGE CONTEXT:\n"
            f"- Subscriber: {LAST_SUBSCRIBER_CONTEXT['user_name']} (@{LAST_SUBSCRIBER_CONTEXT['username']})\n"
            f"- Text: \"{LAST_SUBSCRIBER_CONTEXT['text']}\"\n"
        )

    system_instruction = (
        "Sen @asay_s_blogg kanal adminining shaxsiy aqlli yordamchisisisan.\n\n"
        f"{subscriber_info}\n"
        "ASOSIY QOIDA:\n"
        "Admin qanday savol bersa, o'sha savol nuqtai nazaridan to'g'ridan-to'g'ri javob ber. Xuddi aqlli do'st suhbatidek.\n\n"
        "HECH QACHON:\n"
        "- Javob variantlari ko'rsatma (admin so'ramasa)\n"
        "- Ortiqcha savol berma\n"
        "- Shablon ishlatma\n"
        "- Takroriy salom qilma\n"
        "- 'Quyidagilardan birini tanlang' dema\n\n"
        "FAQAT BITTA ISTISNO:\n"
        "Admin o'zi 'Mijozga nima dey?' yoki 'Qanday javob yozay?' deb so'rasa — o'shanda 2 ta qisqa, odobli javob varianti ber.\n\n"
        "SUHBAT DOIRASI:\n"
        "- Islomiy mavzular (hadis, oyat, duo, tazkiya, axloq)\n"
        "- Kanal strategiyasi va post g'oyalari\n"
        "- Obunachi munosabatlari\n"
        "- Hayotiy masalalar va maslahat\n"
        "- Istalgan mavzuda admin savol bersa — o'sha nuqtadan javob ber\n\n"
        "USLUB:\n"
        "- Til: O'zbek\n"
        "- Qisqa va aniq\n"
        "- Islomiy odobda\n"
        "- Aqlli va samimiy\n"
        "- Keraksiz gap yo'q"
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
                max_tokens=500,
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
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    return "Tushundim, Admin. Qanday yordam beray?"
