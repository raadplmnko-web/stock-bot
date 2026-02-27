import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. خادم الويب لمنع النوم (Flask) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive and running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. الإعدادات وقاعدة البيانات المؤقتة ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
watchlist = {}

# --- 3. الدوال المساعدة (الترجمة والتحليل) ---
def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except: return "لا توجد تفاصيل إضافية حالياً"

def get_full_analysis(symbol):
    try:
        # جلب البيانات من Finnhub
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        candles = requests.get(f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&count=50&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        news = requests.get(f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-12-31&token={FINNHUB_API}").json()
        
        current_price = quote.get('c', 0)
        if current_price == 0: return None
        
        # حساب الزخم و RSI
        prices = candles.get('c', [])
        sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
        
        # حساب RSI مبسط لآخر 14 يوم
        gains = [prices[i] - prices[i-1] for i in range(len(prices)-14, len(prices)) if prices[i] > prices[i-1]]
        losses = [prices[i-1] - prices[i] for i in range(len(prices)-14, len(prices)) if prices[i] < prices[i-1]]
        rs = (sum(gains)/14) / (sum(losses)/14 if losses else 1)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_msg = "شراء (تشبع بيعي) 🟢" if rsi < 30 else "بيع (تشبع شرائي) 🔴" if rsi > 70 else "متعادل ⚪"
        momentum = "إيجابي 🚀" if current_price > sma_20 else "سلبي 📉"
        
        # فلتر الشرعية
        ind = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق للشريعة" if not any(x in ind for x in ['bank', 'finance', 'insur', 'bev']) else "❌ غير مطابق"
        
        # ترجمة الخبر
        headline = news[0]['headline'] if news else "No major news"
        arabic_news = translate_to_arabic(headline)
        
        return {
            "price": current_price, "sharia": sharia, "momentum": momentum,
            "rsi": rsi_msg, "news": arabic_news, "target": round(current_price * 1.05, 2)
        }
    except: return None

# --- 4. معالج الرسائل ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)

    if text == "قائمتي":
        if not watchlist:
            await update.message.reply_text("قائمة المراقبة فارغة.")
        else:
            msg = "📋 **الأسهم تحت المراقبة:**\n"
            for s, info in watchlist.items(): msg += f"- {s}: الهدف {info['target']}$\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        return

    if "راقب" in text:
        symbol = text.replace("راقب", "").strip()
        data = get_full_analysis(symbol)
        if data:
            watchlist[symbol] = {"target": data['target'], "chat_id": chat_id}
            await update.message.reply_text(f"🎯 تم تفعيل الرادار لـ {symbol}\nسأنبهك عند الهدف: {data['target']}$")
        return

    data = get_full_analysis(text)
    if data:
        msg = (f"🍎 **سهم: {text}**\n"
               f"━━━━━━━━━━━━\n"
               f"💰 **السعر:** {data['price']}$\n"
               f"📜 **الشرعية:** {data['sharia']}\n"
               f"📈 **الزخم:** {data['momentum']}\n"
               f"📊 **RSI:** {data['rsi']}\n"
               f"🎯 **الهدف القادم:** {data['target']}$\n"
               f"━━━━━━━━━━━━\n"
               f"📰 **أحدث خبر:**\n_{data['news']}_")
        await update.message.reply_text(msg, parse_mode='Markdown')

# --- 5. وظيفة المراقبة التلقائية (تم إصلاحها للإصدار الجديد) ---
async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    for symbol, info in list(watchlist.items()):
        data = get_full_analysis(symbol)
        if data and data['price'] >= info['target']:
            await context.bot.send_message(chat_id=info['chat_id'], text=f"🔔 **تنبيه عاجل:** سهم {symbol} وصل لهدفك {data['price']}$! 🤑")
            del watchlist[symbol]

# --- 6. التشغيل الرئيسي ---
if __name__ == '__main__':
    Thread(target=run).start()
    if TOKEN:
        # استخدام الطريقة الصحيحة لإصدار بايثون الأخير وتجنب خطأ asyncio
        application = Application.builder().token(TOKEN).build()
        
        # إضافة معالج الرسائل
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # تفعيل المراقبة التلقائية كل دقيقة (60 ثانية)
        job_queue = application.job_queue
        job_queue.run_repeating(check_alerts, interval=60, first=10)
        
        print("Bot is starting...")
        application.run_polling()
