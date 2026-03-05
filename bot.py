import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

async def get_input(prompt):
    # وظيفة ذكية تقرأ الجوال أو الكود من ملف code.txt لتجنب خطأ EOFError
    print(f"⏳ بانتظار المدخلات لـ: {prompt}")
    while True:
        if os.path.exists("code.txt"):
            with open("code.txt", "r") as f:
                data = f.read().strip()
                if data:
                    # تفريغ الملف بعد القراءة للمرة القادمة
                    open("code.txt", "w").close()
                    return data
        await asyncio.sleep(3)

async def main():
    # استخدام StringSession فارغ لإنشاء مفتاح جديد
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # ربط عملية إدخال البيانات بملف code.txt
    await client.start(
        phone=lambda: get_input("رقم الجوال (أدخله في code.txt الآن)"),
        code_callback=lambda: get_input("كود التحقق (أدخله في code.txt الآن)")
    )
    
    print("🔑 المـفـتـاح الـذهـبـي (Session String) هو:")
    print(client.session.save())
    print("👆 انسخ النص الطويل أعلاه وضعه في Render")

if __name__ == "__main__":
    asyncio.run(main())
