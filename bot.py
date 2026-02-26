import requests
import asyncio
import time
from telegram import Bot
import os

# قراءة المتغيرات من Render
TOKEN = os.environ.get("TOKEN")
FINNHUB_API = os.environ.get("FINNHUB_API")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=TOKEN)

async def main():
    print("🚀 البوت يعمل الآن...")

    while True:
        for symbol in ["AAPL", "NVDA", "TSLA", "AMD", "PLTR"]:
            try:
                today = time.strftime('%Y-%m-%d')
                url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={today}&to={today}&token={FINNHUB_API}"

                response = requests.get(url)
                data = response.json()

                if data and isinstance(data, list):
                    headline = data[0]["headline"]
                    message = f"🚀 {symbol}\n📰 {headline}"
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                    print(f"تم إرسال خبر {symbol}")

            except Exception as e:
                print("خطأ:", e)

        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
