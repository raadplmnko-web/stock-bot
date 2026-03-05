import os
import asyncio
from telethon import TelegramClient, events
from telegram import Bot

# جلب الإعدادات من Render
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("CHAT_ID"))
# ضع هنا يوزر القناة التي تريد مراقبتها (مثال: @MyChannel)
TARGET_CHANNEL = "@أدخل_اسم_القناة_هنا" 

async def main():
    # تشغيل حسابك الشخصي كـ "رادار" مع رقم جوالك المسجل
    client = TelegramClient('session_radar', API_ID, API_HASH)
    # بوت الإشعارات
    notification_bot = Bot(token=BOT_TOKEN)
    
    print("📡 الرادار يعمل... بانتظار الكود من تليجرام")

    @client.on(events.NewMessage(chats=TARGET_CHANNEL))
    async def handler(event):
        text = event.raw_text
        # صيد علامة $ في التغريدات أو الأخبار
        if '$' in text:
            await notification_bot.send_message(chat_id=MY_CHAT_ID, text=f"🚀 رادار صيد:\n{text}")

    # التعديل هنا لطلب الكود مباشرة على جوالك وتجنب خطأ EOFError
    await client.start(phone='+966548768843')
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
