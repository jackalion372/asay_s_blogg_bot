import os
import random
import logging
from datetime import datetime
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

# 100% Pre-Verified Sahih Hadiths & Quranic Verses (Original Arabic + English)
EVEN_DAY_DATABASE = [
    {
        "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "translation": "\"Actions are judged by intentions, and every person will get what they intended.\"",
        "citation": "[Sahih al-Bukhari #1, Sahih Muslim #1907]",
        "lesson": "Purity of intention is the essential foundation for all righteous deeds and true peace of mind."
    },
    {
        "arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "translation": "\"A true Muslim is the one from whose tongue and hand other people are safe.\"",
        "citation": "[Sahih al-Bukhari #10, Sahih Muslim #40]",
        "lesson": "Guarding your speech and actions from harming others is a true sign of faith."
    },
    {
        "arabic": "وَتَوَكَّلْ عَلَى الْحَيِّ الَّذِي لَا يَمُوتُ",
        "translation": "\"And rely upon the Ever-Living who does not die.\"",
        "citation": "[Surah Al-Furqan: 58]",
        "lesson": "Placing complete reliance upon the Eternal Creator frees the heart from anxiety and despair."
    },
    {
        "arabic": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ",
        "translation": "\"So remember Me; I will remember you. And be grateful to Me and do not deny Me.\"",
        "citation": "[Surah Al-Baqarah: 152]",
        "lesson": "Remembrance and gratitude bring deep tranquility to the soul and barakah to daily life."
    },
    {
        "arabic": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
        "translation": "\"Whoever believes in Allah and the Last Day should speak good or remain silent.\"",
        "citation": "[Sahih al-Bukhari #6018, Sahih Muslim #47]",
        "lesson": "Mindful speech and dignified silence protect a person from regret and spiritual clutter."
    },
    {
        "arabic": "إِنَّ مَعَ الْعُسْرِ يُسْرًا",
        "translation": "\"Indeed, with hardship comes ease.\"",
        "citation": "[Surah Ash-Sharh: 6]",
        "lesson": "No trial is permanent; relief is always woven into every difficulty by Divine grace."
    }
]

# Profound Classical Wisdom (Original Arabic / Transliteration + English)
ODD_DAY_DATABASE = [
    {
        "speaker": "Hazrat Ali ibn Abi Talib (r.a.)",
        "quote": "Cleanse your heart from envy and malice. The cleaner the heart, the more illuminated one's life becomes.",
        "lesson": "Inner purity and forgiveness are the foundations of lasting spiritual peace."
    },
    {
        "speaker": "Hasan al-Basri (r.a.)",
        "quote": "The world consists of three days: yesterday which has passed; tomorrow which you may not reach; and today which is yours, so make full use of it.",
        "lesson": "Value time and spend every moment of today in goodness and constructive effort."
    },
    {
        "speaker": "Imam ash-Shafi'i (r.a.)",
        "quote": "Time is like a sword. If you do not cut it, it will cut you.",
        "lesson": "Time is your most valuable asset; self-discipline converts it into wisdom."
    },
    {
        "speaker": "Ibn al-Qayyim (r.a.)",
        "quote": "The heart is like a vessel: if it is not filled with the remembrance of God, it will be filled with anxiety.",
        "lesson": "What you choose to nourish your mind with determines your inner peace."
    }
]


def generate_database_post(slot: str = "morning") -> str:
    """Fallback generator using verified local database."""
    today_number = datetime.now().day

    if today_number % 2 == 0:
        item = random.choice(EVEN_DAY_DATABASE)
        html = (
            f"<blockquote><b>{item['arabic']}</b>\n\n"
            f"{item['translation']}\n\n"
            f"<b>{item['citation']}</b></blockquote>\n\n"
            f"<i>{item['lesson']}</i>"
        )
    else:
        item = random.choice(ODD_DAY_DATABASE)
        html = (
            f"<blockquote><b>{item['speaker']} said:</b>\n\n"
            f"\"{item['quote']}\"</blockquote>\n\n"
            f"<i>{item['lesson']}</i>"
        )

    return html


def generate_daily_post(slot: str = "morning") -> str:
    """
    Generates a post using 100% VERIFIED Sahih Hadiths and Quranic verses from the authentic database.
    AI (Groq) is strictly restricted to generating fresh English reflections/lessons based on the authentic source.
    AI DOES NOT write or fabricate Arabic text or citations.
    """
    today_number = datetime.now().day

    if today_number % 2 == 0:
        item = random.choice(EVEN_DAY_DATABASE)
        arabic_part = item['arabic']
        translation_part = item['translation']
        citation_part = item['citation']
        lesson = item['lesson']

        if GROQ_API_KEY:
            try:
                import requests
                prompt = (
                    f"Provide a 1-2 sentence inspiring, practical English reflection for this authentic Islamic verse/hadith:\n"
                    f"Translation: {translation_part}\nCitation: {citation_part}\n"
                    f"Return ONLY the 1-2 sentence reflection in plain English text."
                )
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.6
                    },
                    timeout=8
                )
                if resp.status_code == 200:
                    ai_lesson = resp.json()["choices"][0]["message"]["content"].strip()
                    if ai_lesson and len(ai_lesson) > 10:
                        # Clean quotes if any
                        if ai_lesson.startswith('"') and ai_lesson.endswith('"'):
                            ai_lesson = ai_lesson[1:-1]
                        lesson = ai_lesson
            except Exception as err:
                logger.warning(f"Groq AI reflection generation failed, using static lesson: {err}")

        return (
            f"<blockquote><b>{arabic_part}</b>\n\n"
            f"{translation_part}\n\n"
            f"<b>{citation_part}</b></blockquote>\n\n"
            f"<i>{lesson}</i>"
        )
    else:
        item = random.choice(ODD_DAY_DATABASE)
        speaker_part = item['speaker']
        quote_part = item['quote']
        lesson = item['lesson']

        if GROQ_API_KEY:
            try:
                import requests
                prompt = (
                    f"Provide a 1-2 sentence inspiring, practical English reflection for this classical wisdom quote by {speaker_part}:\n"
                    f"Quote: \"{quote_part}\"\n"
                    f"Return ONLY the 1-2 sentence reflection in plain English text."
                )
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.6
                    },
                    timeout=8
                )
                if resp.status_code == 200:
                    ai_lesson = resp.json()["choices"][0]["message"]["content"].strip()
                    if ai_lesson and len(ai_lesson) > 10:
                        if ai_lesson.startswith('"') and ai_lesson.endswith('"'):
                            ai_lesson = ai_lesson[1:-1]
                        lesson = ai_lesson
            except Exception as err:
                logger.warning(f"Groq AI reflection generation failed, using static lesson: {err}")

        return (
            f"<blockquote><b>{speaker_part} said:</b>\n\n"
            f"\"{quote_part}\"</blockquote>\n\n"
            f"<i>{lesson}</i>"
        )
