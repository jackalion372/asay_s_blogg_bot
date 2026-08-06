import os
from dotenv import load_dotenv

load_dotenv()

# Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "8830144323:AAG5hdNind1Bt2272gZEpqEEu7p5eK5bhdI").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@asay_s_blogg").strip()
EXACT_ADMIN_ID = "8100325700"
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", EXACT_ADMIN_ID).strip()

DEFAULT_PEXELS_KEY = "yGiTash67DOp0P7TjqC8xUJEP30B9v1Lvx9fMc6VVMYFthFnVWpB9BY3"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", DEFAULT_PEXELS_KEY).strip()

POST_TIMEZONE = os.getenv("POST_TIMEZONE", "Asia/Tashkent").strip()


def validate_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    return missing
