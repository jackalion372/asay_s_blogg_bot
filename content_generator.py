import logging
import os
import sys
import random
from datetime import datetime
import pytz
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, POST_TIMEZONE

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

# STRICT NEGATIVE CONSTRAINT & AUTHENTIC CITATION RULE:
STRICT_AUTHENTICITY_RULE = """
CRITICAL AUTHENTICITY RULES:
1. CITATION REQUIREMENT: Every Hadith, Ayah, or classical scholarly quote MUST include its EXACT authentic source reference at the end of the blockquote (e.g., [Sahih al-Bukhari #6481], [Sahih Muslim #2985], [Riyad as-Salihin #145], or [Ihya 'Ulum al-Din - Imam al-Ghazali]).
2. STRICT VERACITY: NEVER invent, fabricate, paraphrase loosely, or hallucinate any Hadith or Quranic verse. Use ONLY well-known, authentic narration texts from Kutub al-Sittah or recognized classical scholars.
3. NO PSYCHOLOGY/POP-PHILOSOPHY: DO NOT use any modern psychology or secular self-help terms. Focus 100% on authentic Islamic spirituality (Tazkiyah, Sabr, Tawakkul, Ikhlas, Akhlaq).
"""

# Base Prompt for SCHOLARLY DAYS (Toq kunlar)
SCHOLARLY_SYSTEM_PROMPT = f"""You are the scholarly author of the Telegram channel "@asay_s_blogg".
{STRICT_AUTHENTICITY_RULE}

Your style rules for SCHOLARLY DAYS (Toq kunlar):
1. Tone: Deep, classical, scholarly, and strictly grounded in authentic Islamic sciences, Hadith commentary, Quranic exegesis, and classical wisdom (Imam Ghazali, Ibn al-Qayyim, Imam Nawawi).
2. HTML Formatting for Telegram:
   - Always wrap quotes, Ayahs, Hadiths inside Telegram HTML <blockquote>...</blockquote> tags.
   - Include the exact book reference/number inside the blockquote!
   - Use <i>...</i> for italicized spiritual insights.
   - Do NOT use Markdown symbols (like ** or ```). ONLY valid Telegram HTML tags (<blockquote>, <b>, <i>).
3. Structure:
   - Section 1: Concise English scholarly reflection on faith, knowledge, or classical Islamic virtue.
   - Section 2: Authentic Arabic text inside <blockquote> with English translation AND exact citation (e.g., [Sahih al-Bukhari #6481]).
   - Section 3: A deep, spiritual takeaway line in <i>...</i>.
"""

# Base Prompt for HUMAN & JOY DAYS (Juft kunlar)
HUMAN_JOY_SYSTEM_PROMPT = f"""You are the warm, human author of the Telegram journal "@asay_s_blogg".
{STRICT_AUTHENTICITY_RULE}

Your style rules for HUMAN & JOY DAYS (Juft kunlar):
1. Tone: Warm, human, uplifting, joy-spreading, gentle, and heart-felt. Focus on bringing peace, gratitude, daily happiness, and hope rooted in faith in Allah.
2. HTML Formatting for Telegram:
   - Wrap inspiring Quranic verses, Hadiths, or Islamic quotes inside Telegram HTML <blockquote>...</blockquote> tags.
   - Include the exact book reference/number inside the blockquote!
   - Use <i>...</i> for a warm, comforting closing prayer or thought.
   - Do NOT use Markdown symbols. ONLY valid Telegram HTML tags.
3. Structure:
   - Section 1: Warm English reflection spreading hope, faith, and gratitude.
   - Section 2: Uplifting Arabic verse/hadith inside <blockquote> with English translation AND exact citation (e.g., [Sahih Muslim #2985]).
   - Section 3: A gentle, comforting closing prayer or thought in <i>...</i>.
"""


def generate_daily_post(slot: str = "morning") -> str:
    """
    Generates a post for @asay_s_blogg with mandatory authentic Hadith/Book citations.
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip()

    tz = pytz.timezone(POST_TIMEZONE)
    now = datetime.now(tz)
    weekday = now.weekday()

    day_number = weekday + 1
    is_odd_day = (day_number % 2 != 0)

    if is_odd_day:
        system_prompt = SCHOLARLY_SYSTEM_PROMPT
        day_theme = "Authentic Islamic Knowledge, Hadith Commentary & Classical Spiritual Wisdom"
    else:
        system_prompt = HUMAN_JOY_SYSTEM_PROMPT
        day_theme = "Faith-based Gratitude, Noble Akhlaq, Joy & Spiritual Peace"

    if slot == "morning":
        slot_prompt = (
            f"Topic theme: {day_theme}. "
            "Context: MORNING POST. Focus on starting the day with morning remembrance (dhikr), intention, faith, and gratitude to Allah."
        )
    else:
        slot_prompt = (
            f"Topic theme: {day_theme}. "
            "Context: EVENING POST. Focus on night reflections, trusting God's decree (tawakkul), contentment of heart, and peace before sleep."
        )

    prompt = (
        f"Write a short, authentic post for @asay_s_blogg. {slot_prompt} "
        "MANDATORY: Include exact Hadith or Quranic book reference number inside <blockquote> (e.g. [Sahih al-Bukhari #6481] or [Surah Al-Baqarah: 153]). "
        "Strictly NO psychology, NO hallucinated texts. "
        "Include English reflection, Arabic quote in <blockquote>...</blockquote> with translation and citation, "
        "and a concluding line in <i>...</i>."
    )

    # 1. Try Groq (Llama-3.3-70b-versatile)
    if groq_key:
        logger.info(f"Using Groq API (Day {day_number} - {'Scholarly' if is_odd_day else 'Human Joy'} - {slot} - Authentic Citations)...")
        try:
            client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,  # Lower temperature for strict factual accuracy
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error using Groq API: {e}")

    # 2. Try Gemini API
    if gemini_key:
        logger.info("Using Google Gemini API...")
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.6,
                    max_output_tokens=300,
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error using Gemini SDK: {e}")

    # 3. Try OpenAI API
    if openai_key:
        logger.info("Using OpenAI API...")
        client = OpenAI(api_key=openai_key)
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating post from OpenAI: {e}")

    raise ValueError("No working AI API key found.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        post = generate_daily_post(slot="morning")
        print(post)
    except Exception as err:
        print(f"Failed to generate post: {err}")
