import os
import asyncio
from telethon import TelegramClient, events
from telegram import Bot

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("CHAT_ID"))

async def get_code():
    print("⏳ بانتظار كتابة الكود في ملف code.txt في GitHub...")
    while True:
        if os.path.exists("code.txt"):
            with open("code.txt", "r") as f:
                code = f.read().strip()
                if code and len(code) >= 5:
                    return code
        await asyncio.sleep(3)

async def main():
    # استخدام اسم جلسة جديد لضمان الاتصال النظيف
    client = TelegramClient('session_radar_final', API_ID, API_HASH)
    notification_bot = Bot(token=BOT_TOKEN)
    
    print("📡 الرادار يحاول الاتصال... راقب تليجرام الآن")
    
    # سيطلب الكود وينتظر كتابته في code.txt
    await client.start(phone='+966548768843', code_callback=get_code)
    print("🚀 تم الاتصال بنجاح! الرادار يراقب القناة الآن.")

    # تم وضع رابط قناتك الخاصة هنا
    @client.on(events.NewMessage(chats='https://t.me/+QfEEuAbj1wA5MGU8'))
    async def handler(event):
        if event.raw_text and '$' in event.raw_text:
            await notification_bot.send_message(chat_id=MY_CHAT_ID, text=f"🎯 صيد جديد من الرادار:\n\n{event.raw_text}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
