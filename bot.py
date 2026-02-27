import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. خادم الويب ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. الإعدادات ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
watchlist = {}

# --- 3. التحليل والترجمة ---
def get_full_analysis(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        candles = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=20&token={FINNHUB_API}").json()
        current_price = quote.get('c', 0)
        if current_price == 0: return None
        
        # زخم RSI مبسط
        prices = candles.get('c', [])
        sma_20 = sum(prices)/len(prices) if prices else current_price
        momentum = "إيجابي 🚀" if current_price > sma_20 else "سلبي 📉"
        
        return {
            "price": current_price,
            "momentum": momentum,
            "target": round(current_price * 1.05, 2)
        }
    except: return None

# --- 4. معالج الرسائل ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)

    if text == "قائمتي":
        msg = "📋 الرادار يراقب:\n" + "\n".join([f"- {s}" for s in watchlist]) if watchlist else "القائمة فارغة."
        await update.message.reply_text(msg)
        return

    if "راقب" in text:
        symbol = text.replace("راقب", "").strip()
        data = get_full_analysis(symbol)
        if data:
            watchlist[symbol] = {"target": data['target'], "chat_id": chat_id}
            await update.message.reply_text(f"🎯 تم تفعيل رادار {symbol} عند {data['target']}$")
        return

    data = get_full_analysis(text)
    if data:
        res = f"🍎 سهم {text}\n💰 السعر: {data['price']}$\n📈 الزخم: {data['momentum']}\n🎯 الهدف: {data['target']}$"
        await update.message.reply_text(res)

# --- 5. وظيفة المراقبة (نسخة متوافقة) ---
async def check_alerts(application):
    while True:
        for symbol, info in list(watchlist.items()):
            data = get_full_analysis(symbol)
            if data and data['price'] >= info['target']:
                await application.bot.send_message(chat_id=info['chat_id'], text=f"🔔 هدف {symbol} تحقق!")
                del watchlist[symbol]
        await asyncio.sleep(60)

# --- 6. التشغيل ---
if __name__ == '__main__':
    Thread(target=run).start()
    if TOKEN:
        # بناء التطبيق بدون JobQueue لتجنب تعليق Render
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # تشغيل المراقبة في الخلفية بطريقة Async المستقرة
        loop = asyncio.get_event_loop()
        loop.create_task(check_alerts(application))
        
        application.run_polling()
