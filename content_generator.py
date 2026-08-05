import logging
import random
from datetime import datetime
import pytz
from config import POST_TIMEZONE

logger = logging.getLogger(__name__)

# ==============================================================================
# EXPANDED 100% SAHIH & PROFOUND LIFE WISDOM DATABASE
# CLEAN FORMATTING: NO CHANNEL LINKS, NO SELF-PRAISE, NO NOISE.
# ==============================================================================

# ODD DAYS (Toq kunlar): Hayotdan olingan chuqur saboqlar va yuksak ma'noli hikmatlar
PROFOUND_LIFE_WISDOM_POSTS = [
    {
        "intro": "The quietest lives often bear the heaviest wisdom. Silence is not the absence of thought, but the stillness where deep understanding is forged.",
        "quote_arabic": "قال علي بن أبي طالب رضي الله عنه:\n«كَلَامُ يَنْفَعُ خَيْرٌ مِنْ كَلَامٍ يَمْنَعُ، وَالصَّمْتُ فِي وَقْتِهِ خَيْرٌ مِنَ الْقَوْلِ فِي غَيْرِ وَقْتِهِ»",
        "quote_english": "\"Beneficial speech is better than speech that hinders, and silence at its proper time is better than speech at an inappropriate time.\"",
        "citation": "[Ghurar al-Hikam - Ali ibn Abi Talib]",
        "closing": "True wisdom is knowing when to speak and when to let quietness teach."
    },
    {
        "intro": "Do not measure a person by their words during ease, but by their character and patience during trials.",
        "quote_arabic": "قال الحسن البصري رحمه الله:\n«حَقِيقَةُ حُسْنِ الْخُلُقِ: بَذْلُ الْمَعْرُوفِ، وَكَفُّ الأَذَى، وَإِطْلاقُ الْوَجْهِ»",
        "quote_english": "\"The essence of good character is: extending kindness, refraining from harm, and maintaining a welcoming disposition.\"",
        "citation": "[Jami' al-'Ulum wal-Hikam - Ibn Rajab]",
        "closing": "Character is the quiet shadow of a person's inner soul."
    },
    {
        "intro": "Time is an unyielding teacher. It reveals the true value of sincerity and exposes the vanity of worldly praise.",
        "quote_arabic": "قال الفضيل بن عياض رحمه الله:\n«تَرْكُ الْعَمَلِ لِأَجْلِ النَّاسِ رِيَاءٌ، وَالْعَمَلُ لِأَجْلِ النَّاسِ شِرْكٌ، وَالإِخْلَاصُ أَنْ يُعَافِيَكَ اللَّهُ مِنْهُمَا»",
        "quote_english": "\"Leaving an action for the sake of people is ostentation, doing an action for the sake of people is shirk, and sincerity is when God saves you from both.\"",
        "citation": "[Al-Adab al-Shar'iyyah - Ibn Muflih]",
        "closing": "Live for the approval of the Creator, not the fleeting applause of the creation."
    },
    {
        "intro": "The greatest lesson life teaches is that peace cannot be bought; it is cultivated within through acceptance and faith.",
        "quote_arabic": "قال الشافعي رحمه الله:\n«عِزُّ النَّفْسِ فِي الْقَنَاعَةِ، وَالرَّاحَةُ فِي الزُّهْدِ»",
        "quote_english": "\"Dignity of the soul is in contentment, and rest of the heart is in detachment from excessive worldly desires.\"",
        "citation": "[Diwan al-Shafi'i]",
        "closing": "Contentment is a kingdom that never perishes."
    },
    {
        "intro": "He who guards his heart from hatred lives in a fortress of peace. Forgiveness is not a favor to others, but a liberation for your own spirit.",
        "quote_arabic": "قال يحيى بن معاذ رحمه الله:\n«لِيَكُنْ حَظُّ الْمُؤْمِنِ مِنْكَ ثَلَاثَةً: إِنْ لَمْ تَنْفَعْهُ فَلَا تَضُرَّهُ، وَإِنْ لَمْ تُفْرِحْهُ فَلَا تَغُمَّهُ، وَإِنْ لَمْ تَمْدَحْهُ فَلَا تَمُمَّهُ»",
        "quote_english": "\"Let a believer's share from you be three: if you cannot benefit him, do not harm him; if you cannot make him happy, do not sadden him; and if you cannot praise him, do not blame him.\"",
        "citation": "[Jami' al-'Ulum wal-Hikam - Ibn Rajab]",
        "closing": "Be a healing presence in a world that often causes pain."
    },
    {
        "intro": "Knowledge without humility is like rain upon hard stone—it runs off without leaving life behind. True learning softens the soul.",
        "quote_arabic": "قال سفيان الثوري رحمه الله:\n«أَوَّلُ الْعِلْمِ الصَّمْتُ، وَالثَّانِي الاِسْتِمَاعُ، وَالثَّالِثُ الْحِفْظُ، وَالرَّابِعُ الْعَمَلُ، وَالْخَامِسُ النَّشْرُ»",
        "quote_english": "\"The first stage of knowledge is silence, the second is listening, the third is memorizing, the fourth is practicing, and the fifth is spreading it.\"",
        "citation": "[Hilyat al-Awliya - Abu Nu'aym]",
        "closing": "Let your actions speak the language of your wisdom."
    },
    {
        "intro": "True dignity is not found in wealth or status, but in standing firm upon noble principles when the world tries to shake you.",
        "quote_arabic": "قال عمر بن الخطاب رضي الله عنه:\n«كُنَّا أَذَلَّ قَوْمٍ، فَأَعَزَّنَا اللَّهُ بِالإِسْلَامِ، فَمَهْمَا ابْتَغَيْنَا العِزَّةَ بِغَيْرِ مَا أَعَزَّنَا اللَّهُ بِهِ أَذَلَّنَا اللَّهُ»",
        "quote_english": "\"We were the most humiliated people, so Allah honored us through Islam. If we seek honor through anything else, Allah will humiliate us.\"",
        "citation": "[Al-Mustadrak - Al-Hakim #207, Sahih]",
        "closing": "Seek honor only in the truth that upholds your soul."
    },
    {
        "intro": "The mind finds rest when it stops trying to control what was destined by the wisdom of the Divine.",
        "quote_arabic": "قال ابن الجوزي رحمه الله:\n«مَنْ أَحَبَّ أَنْ لاَ يَنْقَطِعَ عَمَلُهُ بَعْدَ مَوْتِهِ فَلْيَنْشُرِ الْعِلْمَ»",
        "quote_english": "\"Whoever wishes for their good deeds not to cease after death, let them spread beneficial knowledge.\"",
        "citation": "[Tazkirat al-Sami' - Ibn Jama'ah]",
        "closing": "Leave behind words that illuminate hearts long after you are gone."
    }
]

# EVEN DAYS (Juft kunlar): 100% Sahih va Tekshirilgan Hadislar hamda Oyatlar
AUTHENTIC_SAHIH_POSTS = [
    {
        "intro": "Patience and steadfast faith are the pillars of the believer. In every situation, turn to prayer and reliance upon the Almighty.",
        "quote_arabic": "قال الله تعالى:\n«يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ»",
        "quote_english": "\"O you who have believed, seek help through patience and prayer. Indeed, Allah is with the patient.\"",
        "citation": "[Surah Al-Baqarah: 153]",
        "closing": "Divine support is ever-present for those who persevere."
    },
    {
        "intro": "Purity of intention is the foundation of all righteous deeds. What is done for God remains eternal.",
        "quote_arabic": "قال رسول الله ﷺ:\n«إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى»",
        "quote_english": "\"Actions are judged by intentions, and every person will get what they intended.\"",
        "citation": "[Sahih al-Bukhari #1, Sahih Muslim #1907]",
        "closing": "Purify the intentions of your heart in all that you do."
    },
    {
        "intro": "True tranquility of the heart is not found in material abundance, but in the constant remembrance of the Creator.",
        "quote_arabic": "قال الله تعالى:\n«الَّذِينَ آمَنُوا وَتَطْمَئِنُّ قُلُوبُهُم بِذِكْرِ اللَّهِ ۗ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ»",
        "quote_english": "\"Those who have believed and whose hearts are assured by the remembrance of Allah. Unquestionably, by the remembrance of Allah do hearts find rest.\"",
        "citation": "[Surah Ar-Ra'd: 28]",
        "closing": "Peace is found in quiet dhikr and devotion."
    },
    {
        "intro": "Restraint in speech is a key to wisdom and spiritual protection. Speak good or observe dignified silence.",
        "quote_arabic": "قال رسول الله ﷺ:\n«مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ»",
        "quote_english": "\"Whoever believes in Allah and the Last Day should speak good or remain silent.\"",
        "citation": "[Sahih al-Bukhari #6018, Sahih Muslim #47]",
        "closing": "Dignified speech reflects a noble soul."
    },
    {
        "intro": "Trusting in the mercy and timing of Allah relieves the spirit of heavy anxiety. Relief is promised alongside every hardship.",
        "quote_arabic": "قال الله تعالى:\n«فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ۞ إِنَّ مَعَ الْعُسْرِ يُسْرًا»",
        "quote_english": "\"For truly, with hardship comes ease. Truly, with hardship comes ease.\"",
        "citation": "[Surah Ash-Sharh: 5-6]",
        "closing": "After every dark night, divine ease surely dawns."
    },
    {
        "intro": "Gentleness and compassion elevate human interactions. Being kind brings honor and light into a person's life.",
        "quote_arabic": "قال رسول الله ﷺ:\n«إِنَّ الرِّفْقَ لاَ يَكُونُ فِي شَىْءٍ إِلاَّ زَانَهُ وَلاَ يُنْزَعُ مِنْ شَىْءٍ إِلاَّ شَانَهُ»",
        "quote_english": "\"Verily, gentleness is not in anything except that it beautifies it, and it is not stripped from anything except that it taints it.\"",
        "citation": "[Sahih Muslim #2594]",
        "closing": "Be gentle with God's creation, and the Creator will be merciful with you."
    },
    {
        "intro": "True richness is not measured by earthly possessions, but by the contented peace within one's own soul.",
        "quote_arabic": "قال رسول الله ﷺ:\n«لَيْسَ الْغِنَى عَنْ كَثْرَةِ الْعَرَضِ، وَلَكِنَّ الْغِنَى غِنَى النَّفْسِ»",
        "quote_english": "\"Richness does not lie in the abundance of worldly goods, but richness is the richness of the soul.\"",
        "citation": "[Sahih al-Bukhari #6446, Sahih Muslim #1051]",
        "closing": "Contentment of heart is the greatest wealth."
    },
    {
        "intro": "Forgiveness and pardoning others bring peace to your own heart and elevate your status in the eyes of the Almighty.",
        "quote_arabic": "قال الله تعالى:\n«وَلْيَعْفُوا وَلْيَصْفَحُوا ۗ أَلَا تُحِبُّونَ أَن يَغْفِرَ اللَّهُ لَكُمْ»",
        "quote_english": "\"And let them pardon and overlook. Would you not like that Allah should forgive you?\"",
        "citation": "[Surah An-Nur: 22]",
        "closing": "Forgive others, and live in the spaciousness of mercy."
    }
]


def generate_daily_post(slot: str = "morning") -> str:
    """
    Generates post without any channel links, promo, or self-praise.
    """
    tz = pytz.timezone(POST_TIMEZONE)
    now = datetime.now(tz)
    weekday = now.weekday()  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6

    day_number = weekday + 1
    is_odd_day = (day_number % 2 != 0)  # Mon, Wed, Fri, Sun -> Odd Day (Life Lessons)

    if is_odd_day:
        pool = PROFOUND_LIFE_WISDOM_POSTS
        logger.info("Generating Odd Day post (Profound Life Wisdom & Lessons)...")
    else:
        pool = AUTHENTIC_SAHIH_POSTS
        logger.info("Generating Even Day post (100% Authentic Sahih Hadiths & Verses)...")

    chosen = random.choice(pool)

    # Clean post without any links or hype
    post_html = (
        f"{chosen['intro']}\n\n"
        f"<blockquote>{chosen['quote_arabic']}\n\n"
        f"{chosen['quote_english']}\n\n"
        f"<b>{chosen['citation']}</b></blockquote>\n\n"
        f"<i>{chosen['closing']}</i>"
    )

    return post_html.strip()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- CLEAN POST TEST ---")
    print(generate_daily_post())
