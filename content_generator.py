import random
from datetime import datetime

# 100% Pre-Verified Sahih Hadiths & Quranic Verses
EVEN_DAY_DATABASE = [
    {
        "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "translation": "\"Actions are judged by intentions, and every person will get what they intended.\"",
        "citation": "[Sahih al-Bukhari #1, Sahih Muslim #1907]",
        "lesson": "Barcha qilayotgan amallarimiz xolis Alloh uchun bo'lishi amallarimizning qabul bo'lish shartidir."
    },
    {
        "arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "translation": "\"A true Muslim is the one from whose tongue and hand other Muslims are safe.\"",
        "citation": "[Sahih al-Bukhari #10, Sahih Muslim #40]",
        "lesson": "Chaqimchilik, g'iybat hamda tili va qo'li bilan boshqalarga ozor berishdan saqlanish haqiqiy mo'minlik belgisidir."
    },
    {
        "arabic": "وَتَوَكَّلْ عَلَى الْحَيِّ الَّذِي لَا يَمُوتُ",
        "translation": "\"And rely upon the Ever-Living who does not die.\"",
        "citation": "[Surah Al-Furqan: 58]",
        "lesson": "Faqatgina abadiy va boqiy bo'lgan Zotga tavakkul qilgan qalb hech qachon noumid bo'lmaydi."
    },
    {
        "arabic": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ",
        "translation": "\"So remember Me; I will remember you. And be grateful to Me and do not deny Me.\"",
        "citation": "[Surah Al-Baqarah: 152]",
        "lesson": "Zikr va shukronalik inson qalbiga xotirjamlik va hayotiga baraka olib keladi."
    }
]

# Profound Classical Lessons (Odd Days)
ODD_DAY_DATABASE = [
    {
        "speaker": "Hazrat Ali ibn Abi Tolib (r.a.)",
        "quote": "\"Qalbingizni hasad va g'arazdan poklang. Qalb qanchalik toza bo'lsa, insonning hayoti shunchalik nurlanadi.\"",
        "lesson": "Ichki dunyoni poklash va kechirimlilik ruhiy xotirjamlikning poydevoridir."
    },
    {
        "speaker": "Hasan al-Basriy (r.a.)",
        "quote": "\"Dunyo uch kundan iborat: kechagi kun o'tib ketdi; ertangi kunga yetasizmi-yo'qmi noma'lum; bugungi kun esa sizniki, undan unumli foydalaning.\"",
        "lesson": "Vaqtni qadriga yetish va bugungi har bir lahzani yaxshilikka sarflash donolikdir."
    },
    {
        "speaker": "Imom ash-Shofe'iy (r.a.)",
        "quote": "\"Vaqt bir qilichdir. Agar sen uni kesmasang, u seni kesadi.\"",
        "lesson": "Vaqt insonning eng qimmatbaho sarmoyasidir."
    }
]


def generate_daily_post(slot: str = "morning") -> str:
    """Generates a clean HTML post from the 100% verified database."""
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
            f"<blockquote><b>{item['speaker']} aytadilar:</b>\n\n"
            f"\"{item['quote']}\"</blockquote>\n\n"
            f"<i>{item['lesson']}</i>"
        )

    return html
