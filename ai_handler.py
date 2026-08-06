import os
import logging
from openai import OpenAI
from config import GROQ_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Context memory for tracking subscribers
SUBSCRIBERS_DB = {}  # user_id -> {"name": str, "username": str, "last_seen": str, "msg_count": int}


def test_groq_connection() -> bool:
    """Standalone diagnostic function to test Groq API connectivity."""
    env_key = os.getenv("GROQ_API_KEY", "")
    logger.info(f"--- GROQ DIAGNOSTIC TEST ---")
    logger.info(f"Render ENV GROQ_API_KEY present: {bool(env_key)}")
    logger.info(f"Effective GROQ_API_KEY prefix: {GROQ_API_KEY[:8]}...")

    try:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Test connection. Say OK."}],
            max_tokens=10,
        )
        res_text = response.choices[0].message.content.strip()
        logger.info(f"✅ GROQ API CONNECTION SUCCESSFUL: '{res_text}'")
        return True
    except Exception as e:
        logger.error(f"❌ GROQ API CONNECTION FAILED: {e}", exc_info=True)
        return False


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
    Connects directly to Groq Llama-3.3-70B.
    Forces SINGLE plain-text response, strictly prohibiting numbered lists (1..., 2...).
    """
    clean_prompt = user_prompt.strip().lower()

    # Exact greeting match for clean quick test
    if clean_prompt in ["salom", "assalomu alaykum", "salom alaykum"]:
        return "Va alaykum assalom, bugun qanday yordam kerak?"

    system_instruction = (
        "Sen @asay_s_blogg kanali adminining shaxsiy aqlli AI yordamchisisisan.\n\n"
        "QAT'IY QOIDALAR:\n"
        "1. Admin bilan huddi ChatGPT (GPT-4) kabi to'g'ridan-to'g'ri, samimiy va aqlli muloqot qil.\n"
        "2. Admin savol yoki topshiriq bersa — BITTADA TO'G'RIDAN-TO'G'RI javob ber.\n"
        "3. HECH QACHON raqamlangan ro'yxatlar (1..., 2...) yoki javob variantlarini ko'rsatma.\n"
        "4. HECH QACHON '1. Alaykum assalom, 2. Va alaykum assalom' deb javob berma. Faqat yagona ravon matn yoz.\n"
        "5. Til: O'zbek tili. Javobing qisqa, aniq va foydali bo'lsin."
    )

    # 1. CALL GROQ API (Llama-3.3-70B)
    if GROQ_API_KEY:
        try:
            logger.info(f"Calling Groq API (Llama-3.3-70B) with prompt: '{user_prompt[:40]}...'")
            client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            ai_text = response.choices[0].message.content.strip()
            logger.info(f"Groq API Response received successfully: '{ai_text[:50]}...'")
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
                temperature=0.5,
                max_tokens=600,
            )
            ai_text = response.choices[0].message.content.strip()
            logger.info("OpenAI API Response received successfully.")
            return ai_text
        except Exception as openai_err:
            logger.error(f"❌ OPENAI API ERROR: {openai_err}", exc_info=True)

    return "Tushundim, Admin."


# Run Groq diagnostic check on startup
test_groq_connection()
