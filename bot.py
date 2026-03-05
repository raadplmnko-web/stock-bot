import os
import asyncio
from telethon import TelegramClient, events
from telegram import Bot

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("CHAT_ID"))

async def main():
    # استخدام اسم جلسة جديد لتجنب القفل
    client = TelegramClient('session_new_radar', API_ID, API_HASH)
    notification_bot = Bot(token=BOT_TOKEN)
    
    print("📡 الرادار يحاول الاتصال... راقب تطبيق تليجرام الآن")
    
    # سيطلب الكود، وبما أننا على الجوال، سنحاول إدخاله مرة أخيرة يدوياً
    await client.start(phone='+966548768843')
    
    print("🚀 تم الاتصال بنجاح!")

    @client.on(events.NewMessage(chats='@اسم_القناة'))
    async def handler(event):
        if '$' in event.raw_text:
            await notification_bot.send_message(chat_id=MY_CHAT_ID, text=f"🎯 صيد:\n{event.raw_text}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
