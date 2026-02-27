import os, requests, asyncio, pytz
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from datetime import datetime

# ================== Flask (لإبقاء السيرفر يعمل) ==================
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

# ================== التحليل الكامل ==================
def get_full_analysis(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        candles = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=50&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        news = requests.get(f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-12-31&token={FINNHUB_API}").json()

        current_price = quote.get('c', 0)
        if current_price == 0:
            return None

        prices = candles.get('c', [])
        if len(prices) < 20:
            return None

        sma_20 = sum(prices[-20:]) / 20

        gains = [prices[i] - prices[i-1] for i in range(1, len(prices)) if prices[i] > prices[i-1]]
        losses = [prices[i-1] - prices[i] for i in range(1, len(prices)) if prices[i] < prices[i-1]]

        avg_gain = sum(gains)/14 if gains else 0
        avg_loss = sum(losses)/14 if losses else 1

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # إشارة يومية
        if rsi < 35 and current_price > sma_20:
            signal = "🟢 إشارة دخول يومية"
        elif rsi > 70:
            signal = "🔴 جني أرباح"
        else:
            signal = "⚪ انتظار"

        momentum = "إيجابي 🚀" if current_price > sma_20 else "سلبي 📉"

        # فلتر شرعي مبسط
        ind = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق" if not any(x in ind for x in ['bank', 'finance', 'insur', 'bev']) else "❌ غير مطابق"

        headline = news[0]['headline'] if news else "No news"
        arabic_news = translate_to_arabic(headline)

        target = round(current_price * 1.03, 2)
        stop_loss = round(current_price * 0.985, 2)

        return {
            "price": current_price,
            "sharia": sharia,
            "momentum": momentum,
            "rsi": rsi,
            "signal": signal,
            "news": arabic_news,
            "target": target,
            "stop_loss": stop_loss
        }

    except:
        return None

# ================== الرد على الرسائل ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)

    data = get_full_analysis(text)
    if data:
        msg = (
            f"📊 سهم: {text}\n"
            f"━━━━━━━━━━━━\n"
            f"💰 السعر: {data['price']}$\n"
            f"📜 الشرعية: {data['sharia']}\n"
            f"📈 الزخم: {data['momentum']}\n"
            f"📊 RSI: {round(data['rsi'],2)}\n"
            f"📌 الإشارة: {data['signal']}\n"
            f"🎯 الهدف: {data['target']}$\n"
            f"🛑 وقف الخسارة: {data['stop_loss']}$\n"
            f"━━━━━━━━━━━━\n"
            f"📰 الخبر:\n{data['news']}"
        )
        await update.message.reply_text(msg)

# ================== أفضل 3 فرص تلقائيًا ==================
async def daily_opportunities(application):
    while True:
        if market_is_open():
            symbols = ["TSLA","NVDA","AMD","AAPL","PLTR","META","MSFT"]
            candidates = []

            for symbol in symbols:
                data = get_full_analysis(symbol)
                if not data:
                    continue

                if data["signal"] == "🟢 إشارة دخول يومية" and "✅" in data["sharia"]:
                    score = data["price"]
                    candidates.append((symbol, score, data))

            candidates = sorted(candidates, key=lambda x: x[1], reverse=True)[:3]

            if candidates:
                message = "🚀 أفضل 3 فرص مضاربة الآن:\n\n"
                for symbol, _, data in candidates:
                    message += (
                        f"{symbol}\n"
                        f"💰 {data['price']}$\n"
                        f"🎯 {data['target']}$\n"
                        f"🛑 {data['stop_loss']}$\n"
                        f"━━━━━━━━━━━━\n"
                    )

                await application.bot.send_message(chat_id=list(application.bot_data.values())[0] if application.bot_data else None, text=message)

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
