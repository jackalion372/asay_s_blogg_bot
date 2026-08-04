# @asay_s_blogg — Telegram Kanal Avtomatlashtirish Tizimi

Telegram kanal (@asay_s_blogg) uchun sun'iy intellekt (OpenAI GPT-4o-mini) yordamida to'liq avtomatik, sokin, falsafiy va islomiy ruhdagi kontentlarni yaratib, har kuni belgilangan vaqtda kanalga joylashtirib boruvchi 24/7 bot tizimi.

---

## 📌 1. Loyiha Fayllari Tarkibi

- **`main.py`** — Asosiy bot va scheduler (APScheduler) ishga tushirish fayli.
- **`content_generator.py`** — OpenAI API bilan muloqot qilib, kanal uslubidagi (English + Arabic) post yaratuvchi modul.
- **`telegram_poster.py`** — Telegram Bot API orqali kanalga post yuboruvchi modul.
- **`config.py`** — `.env` faylidan konfiguratsiyalarni yuklovchi va tekshiruvchi fayl.
- **`Dockerfile` & `railway.json`** — Railway.app yoki Render serverlarida 24/7 deploy qilish uchun sozlamalar.
- **`requirements.txt`** — Loyiha uchun zaruriy Python kutubxonalari.

---

## 🛠️ 2. Lokal Muhitda Sinash (Local Setup)

### 1-qadam: Kutubxonalarni o'rnatish
Terminalda loyiha papkasiga o'ting va quyidagi buyruqni bajaring:
```bash
pip install -r requirements.txt
```

### 2-qadam: `.env` faylini yaratish
`.env.example` faylidan nusxa olib, `.env` nomli fayl yarating va o'z kalitlaringizni kiriting:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz_YOUR_BOT_TOKEN
CHANNEL_ID=@asay_s_blogg
ADMIN_USER_ID=YOUR_TELEGRAM_ID_NUMERIC

OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini

POST_TIME=09:00
POST_TIMEZONE=Asia/Tashkent
```

### 3-qadam: Post generatsiyasini alohida sinab ko'rish
Kanalga yubormasdan turib OpenAI qanday post yaratayotganini tekshirish uchun:
```bash
python content_generator.py
```

### 4-qadam: Botni ishga tushirish va sinash
```bash
python main.py
```
Bot ishga tushgach, Telegram'da botingizga kiring va buyruqlarni yuboring:
- `/start` — Bot holatini va sozlangan vaqtlarni ko'rish.
- `/post_now` — Darhol yangi post yaratib, `@asay_s_blogg` kanaliga yuborishni sinab ko'rish.

---

## 🚀 3. GitHub va Railway.app orqali 24/7 Serverga Joylashtirish (Deploy)

### 1-qadam: GitHub Repositoriyaga Yuklash
1. Terminalda quyidagi buyruqlarni ketma-ket bajaring:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for @asay_s_blogg bot"
   ```
2. GitHub.com saytida yangi **Private** repositoriya yarating (masalan: `asay_s_blogg_bot`).
3. GitHub bergan buyruqlar orqali kodingizni yuklang:
   ```bash
   git branch -M main
   git remote add origin https://github.com/USERNAME/asay_s_blogg_bot.git
   git push -u origin main
   ```

### 2-qadam: Railway.app Serverga Ulash
1. [Railway.app](https://railway.app) saytiga kiring va akkauntingizga kiring.
2. **"New Project"** -> **"Deploy from GitHub repo"** tugmasini bosing.
3. Yaratgan `asay_s_blogg_bot` repositoriyangizni tanlang.
4. Project loyihangiz ustiga bosing va **"Variables"** bo'limiga o'ting.
5. `.env` faylingizdagi o'zgaruvchilarni Railway Variables bo'limiga qo'shing:
   - `BOT_TOKEN` = `your_bot_token`
   - `CHANNEL_ID` = `@asay_s_blogg`
   - `OPENAI_API_KEY` = `your_openai_api_key`
   - `OPENAI_MODEL` = `gpt-4o-mini`
   - `POST_TIME` = `09:00`
   - `POST_TIMEZONE` = `Asia/Tashkent`
6. Railway loyihangizni avtomatik build va deploy qiladi. Bot 24/7 rejimda mustaqil ishlay boshlaydi!

---

## 💡 Muhim Eslatmalar
- Bot Telegram kanalingizda **Admin** bo'lishi va *"Post Messages"* (Xabarlarni joylash) huquqiga ega bo'lishi shart.
- OpenAI API hisobingizda balans yetarli ekanligiga ishonch hosil qiling (`gpt-4o-mini` modeli juda arzon bo'lib, oyiga taxminan $1-$2 atrofida sarflaydi).
