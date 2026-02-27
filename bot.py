# bot.py

import os
import requests
import asyncio
import pytz
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

# ================== Flask لإبقاء البوت حي ==================
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ================== المتغيرات ==================
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
watchlist = {}

# ================== التحقق من وقت السوق الأمريكي ==================
def market_is_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:  # عطلة نهاية الأسبوع
        return False
    open_time = now.replace(hour=9, minute=30, second=0)
    close_time = now.replace(hour=16, minute=0, second=0)
    return open_time <= now <= close_time

# ================== ترجمة الأخبار ==================
def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except:
        return "لا توجد تفاصيل إضافية"

# ================== جلب أفضل الأسهم ==================
def get_top_gainers():
    url = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={FINNHUB_API}"
    all_stocks = requests.get(url).json()
    return [s['symbol'] for s in all_stocks if s.get('type') == 'Common Stock']

# ================== التحليل الكامل ==================
def get_full_analysis(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        candles = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=20&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        news = requests.get(f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={yesterday}&to={today}&token={FINNHUB_API}").json()

        current_price = quote.get('c', 0)
        open_price = quote.get('o', 1)
        today_volume = quote.get('v', 0)

        if current_price == 0 or open_price == 0:
            return None

        percent_change = ((current_price - open_price) / open_price) * 100
        volumes = candles.get("v", [])
        avg_volume = sum(volumes)/len(volumes) if volumes else 0
        volume_spike = today_volume > avg_volume * 1.5

        industry = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق" if not any(x in industry for x in ["bank", "finance", "insur", "bev"]) else "❌ غير مطابق"

        positive_keywords = ["earnings", "profit", "growth", "upgrade", "beat", "guidance"]
        headline = news[0]['headline'] if news else ""
        has_positive_news = any(word in headline.lower() for word in positive_keywords)
        arabic_news = translate_to_arabic(headline)

        if current_price < 30 and percent_change >= 3 and volume_spike and "✅" in sharia and has_positive_news:
            return {
                "symbol": symbol,
                "price": current_price,
                "percent_change": round(percent_change,2),
                "target": round(current_price*1.03,2),
                "stop_loss": round(current_price*0.985,2),
                "news": arabic_news,
                "sharia": sharia
            }
        return None
    except:
        return None

# ================== الرد على الرسائل ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    data = get_full_analysis(text)
    if data:
        msg = (
            f"📊 سهم: {text}\n"
            f"💰 السعر: {data['price']}$\n"
            f"📊 التغير اليومي: {data['percent_change']}%\n"
            f"🎯 الهدف: {data['target']}$\n"
            f"🛑 وقف الخسارة: {data['stop_loss']}$\n"
            f"📜 الشرعية: {data['sharia']}\n"
            f"📰 الخبر: {data['news']}"
        )
        await update.message.reply_text(msg)

# ================== الماسح التلقائي ==================
async def daily_opportunities(application):
    while True:
        if market_is_open():
            symbols = get_top_gainers()[:100]  # أفضل 100 سهم نشط
            candidates = []

            for symbol in symbols:
                data = get_full_analysis(symbol)
                if data:
                    candidates.append((symbol, data["percent_change"], data))

            candidates = sorted(candidates, key=lambda x: x[1], reverse=True)[:3]

            if candidates:
                message = "🚀 أفضل 3 فرص اليوم:\n\n"
                for _, _, data in candidates:
                    message += (
                        f"{data['symbol']}\n"
                        f"💰 {data['price']}$\n"
                        f"📊 {data['percent_change']}%\n"
                        f"🎯 {data['target']}$\n"
                        f"🛑 {data['stop_loss']}$\n"
                        f"📜 {data['sharia']}\n"
                        f"📰 {data['news']}\n"
                        f"━━━━━━━━━━━━\n"
                    )

                await application.bot.send_message(chat_id=os.getenv('CHAT_ID'), text=message)

        await asyncio.sleep(1800)  # كل 30 دقيقة

# ================== تشغيل البوت ==================
if __name__ == '__main__':
    Thread(target=run).start()

    if TOKEN:
        app_tg = Application.builder().token(TOKEN).build()
        app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        loop = asyncio.get_event_loop()
        loop.create_task(daily_opportunities(app_tg))
        app_tg.run_polling() 
