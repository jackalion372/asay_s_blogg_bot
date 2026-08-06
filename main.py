import asyncio
import logging
import os
from config import BOT_TOKEN, validate_config, EXACT_ADMIN_ID
from bot import build_application, start_web_server

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """Main application launcher."""
    missing = validate_config()
    if missing:
        logger.warning(f"Missing config variables: {', '.join(missing)}")

    if not BOT_TOKEN:
        logger.error("Cannot start bot without BOT_TOKEN.")
        return

    application = build_application()

    # Start HTTP web server in background before Telegram polling
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())

    logger.info(f"Bot starting with strict Admin ID filtering ({EXACT_ADMIN_ID}) & Modular Architecture...")
    application.run_polling()


if __name__ == "__main__":
    main()
