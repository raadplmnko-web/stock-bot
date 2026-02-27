import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

app = Flask('')
@app.route('/')
def home(): return "Bot is alive and running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
watchlist = {}

def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except: return "لا توجد تفاصيل إضافية"

def get_full_analysis(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        candles = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=50&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        news = requests.get(f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-12-31&token={FINNHUB_API}").json()
        
        current_price = quote.get('c', 0)
        if current_price == 0: return None
        
        # 1. حساب الزخم و RSI مبسط
        prices = candles.get('c', [])
        sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
        
        # حساب RSI تقريبي
        gains = [prices[i] - prices[i-1] for i in range(1, len(prices)) if prices[i] > prices[i-1]]
        losses = [prices[i-1] - prices[i] for i in range(1, len(prices)) if prices[i] < prices[i-1]]
        avg_gain = sum(gains)/14 if gains else 0
        avg_loss = sum(losses)/14 if losses else 1
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        rsi_msg = "شراء (تشبع بيعي) 🟢" if rsi < 30 else "بيع (تشبع شرائي) 🔴" if rsi > 70 else "متعادل ⚪"
        momentum = "إيجابي 🚀" if current_price > sma_20 else "سلبي 📉"
        
        # 2. الشرعية
        ind = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق" if not any(x in ind for x in ['bank', 'finance', 'insur', 'bev']) else "❌ غير مطابق"
        
        # 3. ترجمة الخبر
        headline = news[0]['headline'] if news else "No news"
        arabic_news = translate_to_arabic(headline)
        
        return {
            "price": current_price, "sharia": sharia, "momentum": momentum,
            "rsi": rsi_msg, "news": arabic_news, "target": round(current_price * 1.05, 2)
        }
    except: return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)

    if text == "قائمتي":
        if not watchlist:
            await update.message.reply_text("قائمة المراقبة فارغة حالياً.")
        else:
            msg = "📋 **قائمة المراقبة الخاصة بك:**\n"
            for s, info in watchlist.items():
                msg += f"- {s}: الهدف {info['target']}$\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return

    if "راقب" in text:
        symbol = text.replace("راقب", "").strip()
        data = get_full_analysis(symbol)
        if data:
            watchlist[symbol] = {"target": data['target'], "chat_id": chat_id}
            await update.message.reply_text(f"🎯 تم تفعيل الرادار لـ {symbol}\nسأقوم بتنبيهك عند السعر: {data['target']}$")
        return

    data = get_full_analysis(text)
    if data:
        msg = (f"🍎 **سهم: {text}**\n"
               f"━━━━━━━━━━━━\n"
               f"💰 **السعر:** {data['price']}$\n"
               f"📜 **الشرعية:** {data['sharia']}\n"
               f"📈 **الزخم:** {data['momentum']}\n"
               f"📊 **مؤشر RSI:** {data['rsi']}\n"
               f"🎯 **الهدف:** {data['target']}$\n"
               f"━━━━━━━━━━━━\n"
               f"📰 **الخبر الأخير:**\n_{data['news']}_")
        await update.message.reply_text(msg, parse_mode='Markdown')

async def auto_monitor(application):
    while True:
        for symbol, info in list(watchlist.items()):
            data = get_full_analysis(symbol)
            if data and data['price'] >= info['target']:
                await application.bot.send_message(chat_id=info['chat_id'], text=f"🔔 **تنبيه عاجل**\nسهم {symbol} حقق الهدف المخطط له: {data['price']}$ 🤑")
                del watchlist[symbol]
        await asyncio.sleep(60)

if __name__ == '__main__':
    Thread(target=run).start()
    if TOKEN:
        app_tg = Application.builder().token(TOKEN).build()
        app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        loop = asyncio.get_event_loop()
        loop.create_task(auto_monitor(app_tg))
        app_tg.run_polling()
