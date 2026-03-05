import os
import asyncio
from telethon import TelegramClient, events
from telegram import Bot

# إعدادات الرادار من Render
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("CHAT_ID"))
# ضع يوزر القناة هنا (تأكد أنك مشترك فيها بحسابك الشخصي)
TARGET_CHANNEL = "@اسم_القناة_هنا" 

async def main():
    # تشغيل الحساب الشخصي كـ "رادار"
    client = TelegramClient('session_radar', API_ID, API_HASH)
    # بوت التنبيهات الذي سيرسل لك الخبر
    notification_bot = Bot(token=BOT_TOKEN)
    
    print("📡 الرادار يعمل الآن... بانتظار الكود أو الرسائل")

    @client.on(events.NewMessage(chats=TARGET_CHANNEL))
    async def handler(event):
        text = event.raw_text
        # الفلتر لصيد الأسهم (علامة $)
        if '$' in text:
            await notification_bot.send_message(chat_id=MY_CHAT_ID, text=f"🚀 رادار: {text}")

    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
