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

# قائمة المراقبة العالمية (تُحفظ في الذاكرة)
watchlist = {}

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
MY_CHAT_ID = "687056332"

def get_detailed_data(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        # جلب بيانات الشموع لآخر 20 يوم للزخم
        res = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=20&token={FINNHUB_API}").json()
        
        current_price = quote.get('c', 0)
        if current_price == 0: return None
        
        # حساب المتوسط البسيط لـ 20 يوم
        prices = res.get('c', [])
        sma_20 = sum(prices) / len(prices) if prices else current_price
        momentum = "قوي 🚀" if current_price > sma_20 else "ضعيف 📉"
        
        industry = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق" if not any(x in industry for x in ['bank', 'finance', 'insur', 'bev']) else "❌ غير مطابق"
        
        return {
            "price": current_price,
            "sharia": sharia,
            "momentum": momentum,
            "target": round(current_price * 1.05, 2), # هدف 5%
            "stop": round(current_price * 0.95, 2)
        }
    except: return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)
    
    # 1. حالة المراقبة
    if "راقب" in text:
        symbol = text.replace("راقب", "").strip().upper()
        data = get_detailed_data(symbol)
        if data:
            watchlist[symbol] = {"target": data['target'], "chat_id": chat_id}
            await update.message.reply_text(f"🎯 تم تفعيل الرادار لـ {symbol}\nسأقوم بتنبيهك عند وصول السعر لـ {data['target']}$")
        return

    # 2. حالة تحليل الزخم والإيجابية
    if any(x in text for x in ["زخم", "إيجابي"]):
        symbol = text.split()[0]
        data = get_detailed_data(symbol)
        if data:
            await update.message.reply_text(f"📊 تحليل {symbol}:\nالزخم: {data['momentum']}\nالحالة: {'إيجابي جداً ✅' if data['momentum'] == 'قوي 🚀' else 'سلبي ⚠️'}")
        return

    # 3. تحليل السهم العادي
    data = get_detailed_data(text)
    if data:
        msg = (f"🍎 سهم: {text}\n"
               f"💰 السعر: {data['price']}$\n"
               f"📜 الشرعية: {data['sharia']}\n"
               f"🚀 الهدف: {data['target']}$\n"
               f"📉 الوقف: {data['stop']}$")
        await update.message.reply_text(msg)

# وظيفة فحص الأهداف تلقائياً كل دقيقة
async def check_targets(application):
    while True:
        for symbol, info in list(watchlist.items()):
            data = get_detailed_data(symbol)
            if data and data['price'] >= info['target']:
                await application.bot.send_message(chat_id=info['chat_id'], text=f"🔔 تنبيه: سهم {symbol} حقق الهدف الأول {data['price']}$! 🤑")
                del watchlist[symbol]
        await asyncio.sleep(60)

if __name__ == '__main__':
    Thread(target=run).start()
    if TOKEN:
        app_tg = Application.builder().token(TOKEN).build()
        app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # تشغيل فحص الأهداف في الخلفية
        loop = asyncio.get_event_loop()
        loop.create_task(check_targets(app_tg))
        
        app_tg.run_polling()
