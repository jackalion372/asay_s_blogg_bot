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
    Gives a SINGLE, DIRECT, SMART answer to Admin questions.
    ZERO reply options or choices logic.
    """
    system_instruction = (
        "Sen @asay_s_blogg kanal adminining (ID: 8100325700) shaxsiy aqlli yordamchisisisan.\n\n"
        "ASOSIY QOIDA:\n"
        "Admin qanday savol bersa, o'sha savol nuqtai nazaridan to'g'ridan-to'g'ri va bir dona javob ber. Xuddi aqlli do'st suhbatidek.\n\n"
        "HECH QACHON:\n"
        "- Javob variantlarini ko'rsatma\n"
        "- Ortiqcha savol berma\n"
        "- Shablon ishlatma\n"
        "- Takroriy salom qilma\n"
        "- 'Quyidagilardan birini tanlang' dema\n\n"
        "SUHBAT DOIRASI:\n"
        "- Islomiy mavzular (hadis, oyat, duo, tazkiya, axloq)\n"
        "- Kanal strategiyasi va post g'oyalari\n"
        "- Obunachi munosabatlari va boshqaruv\n"
        "- Hayotiy masalalar va maslahat\n"
        "- Istalgan mavzuda admin savol bersa — o'sha nuqtadan to'g me'yorida javob ber\n\n"
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
                max_tokens=450,
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
                max_tokens=450,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Chat Error: {e}")

    return "Tushundim, Admin. Qanday yordam beray?"
