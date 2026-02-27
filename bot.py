import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. خادم ويب بسيط ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. الإعدادات ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
watchlist = {}

# --- 3. جلب بيانات السهم ---
def get_stock_data(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
        res = requests.get(url).json()
        return res.get('c', 0)
    except: return 0

# --- 4. معالج الرسائل ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().upper()
    chat_id = update.message.chat_id

    if text == "قائمتي":
        msg = "📋 نراقب حالياً:\n" + "\n".join(list(watchlist.keys())) if watchlist else "القائمة فارغة."
        await update.message.reply_text(msg)
        return

    price = get_stock_data(text)
    if price > 0:
        target = round(price * 1.05, 2)
        watchlist[text] = {"target": target, "chat_id": chat_id}
        res = f"🍎 سهم {text}\n💰 السعر الحالي: {price}$\n🎯 الهدف التلقائي: {target}$\n✅ تم تفعيل الرادار لهذا السهم."
        await update.message.reply_text(res)
    else:
        await update.message.reply_text("❌ لم أتمكن من العثور على السهم. تأكد من الرمز (مثلاً: AAPL)")

# --- 5. وظيفة الرادار ---
async def monitor_stocks(application):
    while True:
        for symbol, info in list(watchlist.items()):
            current = get_stock_data(symbol)
            if current >= info['target']:
                await application.bot.send_message(chat_id=info['chat_id'], text=f"🔔 تنبيه: {symbol} وصل لهدفه {current}$!")
                del watchlist[symbol]
        await asyncio.sleep(60)

# --- 6. التشغيل ---
def main():
    if not TOKEN: return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل الرادار في الخلفية
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_stocks(application))
    
    application.run_polling()

if __name__ == '__main__':
    Thread(target=run).start()
    main()
