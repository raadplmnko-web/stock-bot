import os
import requests
import asyncio
from datetime import datetime
from telegram import Bot

# المفاتيح من Render
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
CHAT_ID = "ضع_هنا_رقم_حسابك_في_تليجرام" 

STOCKS_TO_WATCH = ["AAPL", "TSLA", "NVDA", "VEEA"] # قائمة الأسهم

async def check_stocks():
    bot = Bot(token=TOKEN)
    sent_news = set() # لمنع تكرار إرسال نفس الخبر

    while True:
        for symbol in STOCKS_TO_WATCH:
            # جلب البيانات
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
            news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
            
            price_data = requests.get(quote_url).json()
            news_data = requests.get(news_url).json()

            current_price = price_data.get('c', 0)
            change_percent = price_data.get('dp', 0) # نسبة التغير اليومي

            # شرط الزخم أو الخبر الإيجابي
            if change_percent > 2 or (news_data and news_data[0]['id'] not in sent_news):
                news_headline = news_data[0]['headline'] if news_data else "زخم صاعد قوي!"
                if news_data: sent_news.add(news_data[0]['id'])

                message = (
                    f"⚡️ **تنبيه زخم — {datetime.now().strftime('%H:%M')}** 🇸🇦\n\n"
                    f"🔶 الرمز <- {symbol} 🇺🇸\n"
                    f"📈 التغير <- {change_percent}%\n"
                    f"💰 السعر <- {current_price} دولار\n"
                    f"📰 **الخبر:** {news_headline}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
        
        await asyncio.sleep(60) # انتظر دقيقة ثم افحص مرة أخرى

if __name__ == '__main__':
    asyncio.run(check_stocks())
