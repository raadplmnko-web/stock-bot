import os
import asyncio
from telethon import TelegramClient, events
from telegram import Bot

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("CHAT_ID"))

async def main():
    # إنشاء العميل
    client = TelegramClient('session_name', API_ID, API_HASH)
    notification_bot = Bot(token=BOT_TOKEN)
    
    # محاولة الدخول برقمك والكود الذي وصلك تلقائياً
    # استبدل XXXXX بالرقم الذي سيصلك الآن
    await client.start(phone='+966548768843', code_callback=lambda: '23385') 
    
    print("🚀 نجح الاتصال! الرادار يعمل الآن.")

    @client.on(events.NewMessage(chats='@اسم_قناتك'))
    async def handler(event):
        if '$' in event.raw_text:
            await notification_bot.send_message(chat_id=MY_CHAT_ID, text=f"🎯 صيد:\n{event.raw_text}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
