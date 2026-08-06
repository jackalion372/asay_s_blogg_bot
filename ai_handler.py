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
    NEVER gives multiple options unless Admin explicitly asks 'Mijozga nima deb javob beray?'.
    """
    lower_prompt = user_prompt.lower()
    
    # Check if admin explicitly asked for subscriber reply options
    is_asking_subscriber_reply = any(phrase in lower_prompt for phrase in [
        "mijozga nima deb javob beray", 
        "mijozga nima dey", 
        "qanday javob yozay", 
        "obunachiga nima dey"
    ])
    
    subscriber_info = ""
    if LAST_SUBSCRIBER_CONTEXT["text"]:
        subscriber_info = (
            f"LATEST SUBSCRIBER MESSAGE CONTEXT:\n"
            f"- Subscriber: {LAST_SUBSCRIBER_CONTEXT['user_name']} (@{LAST_SUBSCRIBER_CONTEXT['username']})\n"
            f"- Text: \"{LAST_SUBSCRIBER_CONTEXT['text']}\"\n"
        )

    if is_asking_subscriber_reply:
        option_instruction = (
            "Admin is explicitly asking how to reply to the latest subscriber. "
            "Provide EXACTLY 2 short, polite Uzbek reply options tailored to the subscriber's message."
        )
    else:
        option_instruction = (
            "Give a SINGLE, DIRECT, SMART answer to the Admin's query. "
            "STRICT RULE: DO NOT provide multiple reply options, DO NOT say 'quyidagilardan birini tanlang', DO NOT provide choices. Answer directly as a wise executive friend."
        )

    system_instruction = (
        "Sen @asay_s_blogg kanal adminining (ID: 8100325700) shaxsiy aqlli yordamchisisisan.\n\n"
        f"{subscriber_info}\n"
        f"{option_instruction}\n\n"
        "STRICT RULES:\n"
        "- Answer directly in Uzbek, concise, intelligent, and respectful.\n"
        "- NO repetitive greetings ('Assalomu alaykum').\n"
        "- NO modern psychology jargon, NO secular self-help terms.\n"
        "- Maintain authentic Islamic dignity and wisdom."
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
