import asyncio
import logging
import sys
from content_generator import generate_daily_post
from telegram_poster import send_post_to_channel

logging.basicConfig(level=logging.INFO)

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_live_video_post():
    print("1. Groq AI orqali post matni va Pexels API orqali real HD tabiat videosi olinmoqda...")
    post_content = generate_daily_post(slot="evening")
    
    print("\n--- YARATILGAN MATN ---")
    print(post_content)
    print("------------------------\n")
    
    print("2. Video bilan birgalikda @asay_s_blogg Telegram kanaliga joylanmoqda...")
    success = await send_post_to_channel(post_content, attach_video=True)
    if success:
        print("[SUCCESS] Real HD tabiat videosi va post matni kanalingizga muvaffaqiyatli joylashtirildi!")
    else:
        print("[ERROR] Video postni joylashda xatolik.")

if __name__ == "__main__":
    asyncio.run(test_live_video_post())
