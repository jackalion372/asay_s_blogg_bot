import os
import logging
from openai import OpenAI
from config import GROQ_API_KEY, OPENAI_API_KEY, EXACT_ADMIN_ID

logger = logging.getLogger(__name__)

# Memory for subscriber context & unique subscribers tracking
LAST_SUBSCRIBER_CONTEXT = {
    "user_name": "",
    "username": "",
    "user_id": "",
    "text": "",
    "time": ""
}

SUBSCRIBERS_DB = {}  # user_id -> {"name": str, "username": str, "last_seen": str, "msg_count": int}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    """Updates last subscriber context and tracks subscriber history."""
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
    Uses Groq Llama-3.3-70B. Speaks Uzbek, short, Islamic, intelligent.
    """
    subscriber_info = ""
    if LAST_SUBSCRIBER_CONTEXT["text"]:
        subscriber_info = (
            f"LATEST SUBSCRIBER MESSAGE CONTEXT:\n"
            f"- Subscriber: {LAST_SUBSCRIBER_CONTEXT['user_name']} (@{LAST_SUBSCRIBER_CONTEXT['username']})\n"
            f"- Text: \"{LAST_SUBSCRIBER_CONTEXT['text']}\"\n"
            f"Rule: If Admin asks 'Mijozga nima deb javob beray?' or asks for advice, provide 2 concise, polite Uzbek reply options right away.\n"
        )

    system_instruction = (
        f"You are the quiet executive assistant for {admin_name}, owner of @asay_s_blogg channel.\n"
        f"{subscriber_info}\n"
        "STRICT STYLE RULES:\n"
        "1. Be quiet, concise, direct, and intelligent in Uzbek.\n"
        "2. DO NOT chatter, DO NOT say repetitive greetings ('Assalomu alaykum'), DO NOT nag the admin.\n"
        "3. Strictly NO modern psychology jargon, NO secular self-help terms.\n"
        "4. Always maintain authentic Islamic dignity, wisdom, and clarity."
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
