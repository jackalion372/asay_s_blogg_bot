import logging

logger = logging.getLogger(__name__)

SUBSCRIBERS_DB = {}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    if user_id not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id] = {"name": user_name, "username": username, "last_seen": time_str, "msg_count": 1}
    else:
        SUBSCRIBERS_DB[user_id]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id]["msg_count"] += 1
