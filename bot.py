import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# جلب البيانات من Render
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

async def get_session():
    # إنشاء جلسة مؤقتة لاستخراج المفتاح
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("🔑 المـفـتـاح الـذهـبـي (Session String) هو:")
        print(client.session.save())
        print("👆 انسخ النص الطويل أعلاه وضعه في Render")

if __name__ == "__main__":
    asyncio.run(get_session())
