import os
import re
import logging
import urllib.parse
import requests
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

SUBSCRIBERS_DB = {}


def update_subscriber_context(user_name: str, username: str, user_id: str, text: str, time_str: str):
    if user_id not in SUBSCRIBERS_DB:
        SUBSCRIBERS_DB[user_id] = {"name": user_name, "username": username, "last_seen": time_str, "msg_count": 1}
    else:
        SUBSCRIBERS_DB[user_id]["last_seen"] = time_str
        SUBSCRIBERS_DB[user_id]["msg_count"] += 1


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
        "You are an elite, highly intelligent AI Executive Copilot for the Administrator of @asay_s_blogg. "
        "CRITICAL INSTRUCTIONS:\n"
        "1. Provide deep, accurate, concise, and highly professional answers (ChatGPT-4o level quality).\n"
        "2. Avoid fluff, filler text, or time-wasting pleasantries. Get straight to the most practical, advanced solution.\n"
        "3. When presented with a problem or request, structure your answer logically with key bullet points or step-by-step solutions.\n"
        "4. Always match the user's language (Uzbek, English, or Russian) with high fluency and professional tone.\n"
        "5. If web search context is provided below, incorporate the real-time facts seamlessly.\n"
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

