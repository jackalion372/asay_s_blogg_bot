import os
import re
import logging
import urllib.parse
import requests
from config import GROQ_API_KEY

import json

logger = logging.getLogger(__name__)

SUBSCRIBERS_DB_FILE = "subscribers.json"


def load_subscribers_db() -> dict:
    if os.path.exists(SUBSCRIBERS_DB_FILE):
        try:
            with open(SUBSCRIBERS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading subscribers DB: {e}")
    return {}


def save_subscribers_db():
    try:
        with open(SUBSCRIBERS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(SUBSCRIBERS_DB, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving subscribers DB: {e}")


SUBSCRIBERS_DB = load_subscribers_db()


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    user_id_str = str(user_id)

    # Automatically purge demo entries as soon as a real user arrives
    demo_keys = [uid for uid, info in SUBSCRIBERS_DB.items() if info.get("is_demo", False)]
    if demo_keys:
        for dkey in demo_keys:
            SUBSCRIBERS_DB.pop(dkey, None)
        logger.info(f"Purged {len(demo_keys)} demo subscriber entries for real user {user_id_str}.")

    if user_id_str not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id_str] = {
            "name": user_name,
            "username": username,
            "user_id": user_id_str,
            "last_seen": time_str,
            "msg_count": 1,
            "is_demo": False
        }
    else:
        SUBSCRIBERS_DB[user_id_str]["name"] = user_name
        SUBSCRIBERS_DB[user_id_str]["username"] = username
        SUBSCRIBERS_DB[user_id_str]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id_str]["msg_count"] += 1
        SUBSCRIBERS_DB[user_id_str]["is_demo"] = False
    save_subscribers_db()


def search_web(query: str, max_results: int = 5) -> str:
    """Live web search via DuckDuckGo to fetch real-time information."""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
            clean_snippets = []
            for s in snippets[:max_results]:
                text = re.sub(r'<.*?>', '', s).strip()
                if text:
                    clean_snippets.append(text)
            if clean_snippets:
                return "\n---\n".join(clean_snippets)
    except Exception as e:
        logger.warning(f"Web search error: {e}")
    return ""


def ask_admin_ai_copilot(user_query: str, history: list = None) -> str:
    """
    Professional ChatGPT-style AI Copilot for Admin.
    Provides advanced, practical, clear solutions and fetches live web search results when needed.
    """
    if not GROQ_API_KEY:
        return "❌ AI API kaliti (GROQ_API_KEY) sozlanmagan. Iltimos, .env faylini tekshiring."

    # Determine if web search is needed
    search_keywords = ["qidir", "izla", "search", "yangilik", "bugun", "xabar", "so'nggi", "latest", "news", "google", "internet"]
    query_lower = user_query.lower()
    needs_search = any(kw in query_lower for kw in search_keywords)

    web_data = ""
    if needs_search:
        clean_query = user_query
        for kw in search_keywords:
            clean_query = clean_query.replace(kw, "")
        clean_query = clean_query.strip() or user_query
        web_data = search_web(clean_query)

    sys_prompt = (
        "You are an elite Islamic AI Executive Copilot and Assistant for the Administrator of the Telegram channel @asay_s_blogg. "
        "YOUR PERSONA & TONE:\n"
        "- Ethically Islamic & Serene Tone: Speak with high dignity, warmth, and Islamic etiquette ('Assalomu alaykum', 'Bismillah', 'Alhamdulillah'). Your wisdom is deeply aligned with the serene, philosophical, and Islamic identity of @asay_s_blogg.\n"
        "- Admin Executive Assistant: You assist the Admin in executing tasks, generating channel posts, solving complex technical/business problems, and strategy.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Provide deep, accurate, concise, and highly practical answers (ChatGPT-4o level quality).\n"
        "2. Avoid fluff, useless filler text, or time-wasting chatter. Deliver clear, structured, step-by-step solutions to any problem or task.\n"
        "3. Zero Hallucination for Sources: When referring to Quranic verses or Hadiths, maintain strict authenticity.\n"
        "4. Always match the user's language (Uzbek, English, or Russian) fluently with high respect and Islamic grace.\n"
        "5. Seamlessly integrate real-time web search facts whenever internet search results are provided.\n"
    )

    if web_data:
        sys_prompt += f"\n\n[REAL-TIME LIVE INTERNET SEARCH RESULTS]:\n{web_data}\n"

    messages = [{"role": "system", "content": sys_prompt}]

    if history:
        for item in history[-6:]:  # Keep recent history
            messages.append(item)

    messages.append({"role": "user", "content": user_query})

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 1200
            },
            timeout=15
        )
        if resp.status_code == 200:
            ai_reply = resp.json()["choices"][0]["message"]["content"].strip()
            return ai_reply
        else:
            return f"❌ AI xatoligi (HTTP {resp.status_code}): {resp.text}"
    except Exception as err:
        logger.error(f"Error during AI Copilot call: {err}")
        return f"❌ AI ulanishida xatolik yuz berdi: {err}"

