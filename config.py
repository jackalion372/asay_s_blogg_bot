import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# Telegram Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "8830144323:AAG5hdNind1Bt2272gZEpqEEu7p5eK5bhdI").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@asay_s_blogg").strip()
EXACT_ADMIN_ID = "8100325700"
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", EXACT_ADMIN_ID).strip()

# Aesthetic Media Sources
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "yGiTash67DOp0P7TjqC8xUJEP30B9v1Lvx9fMc6VVMYFthFnVWpB9BY3").strip()

# Schedule Settings
POST_TIME = os.getenv("POST_TIME", "09:00").strip()
POST_TIMEZONE = os.getenv("POST_TIMEZONE", "Asia/Tashkent").strip()


def validate_config():
    """Validates presence of critical variables."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    return missing
