import logging

logger = logging.getLogger(__name__)

# Context memory for tracking subscribers (NO AI)
SUBSCRIBERS_DB = {}  # user_id -> {"name": str, "username": str, "last_seen": str, "msg_count": int}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    """Tracks unique subscribers and their latest message time."""
    if user_id not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id] = {"name": user_name, "username": username, "last_seen": time_str, "msg_count": 1}
    else:
        SUBSCRIBERS_DB[user_id]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id]["msg_count"] += 1
