import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# Telegram Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@asay_s_blogg").strip()
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "8100325700").strip()

# AI Credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# Aesthetic Media Sources
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PINTEREST_BOARD_URL = os.getenv("PINTEREST_BOARD_URL", "").strip()

# Schedule Settings
POST_TIME = os.getenv("POST_TIME", "09:00").strip()
POST_TIMEZONE = os.getenv("POST_TIMEZONE", "Asia/Tashkent").strip()


def validate_config():
    """Validates presence of critical variables."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GROQ_API_KEY and not GEMINI_API_KEY and not OPENAI_API_KEY:
        missing.append("AI_API_KEY (Groq, Gemini, or OpenAI)")
    return missing
