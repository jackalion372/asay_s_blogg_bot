import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@asay_s_blogg").strip()
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

POST_TIME = os.getenv("POST_TIME", "09:00").strip()
POST_TIMEZONE = os.getenv("POST_TIMEZONE", "Asia/Tashkent").strip()


def validate_config() -> list[str]:
    """Validates that necessary environment variables are set."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    return missing
