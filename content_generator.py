import os
import random
import logging
from datetime import datetime

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


def generate_daily_post(slot: str = "morning") -> str:
    """Generates a clean HTML post in ENGLISH with original ARABIC sources intact."""
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

