import os, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 1. تشغيل السيرفر لضمان بقاء البوت حياً
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# 2. إعدادات المفاتيح
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# 3. دالة جلب البيانات والتحليل المباشر
def get_analysis(symbol):
    try:
        # جلب السعر الحالي
        res = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        price = res.get('c', 0)
        if price == 0: return None
        
        # تحليل بسيط للاتجاه
        change = res.get('d', 0)
        status = "📈 صاعد" if change > 0 else "📉 هابط"
        
        return {
            "price": price,
            "status": status,
            "target": round(price * 1.05, 2)
        }
    except: return None

# 4. الرد على الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    symbol = update.message.text.strip().upper()
    data = get_analysis(symbol)
    
    if data:
        msg = (f"🍎 **سهم: {symbol}**\n"
               f"━━━━━━━━━━━━\n"
               f"💰 **السعر:** {data['price']}$\n"
               f"📊 **الحالة:** {data['status']}\n"
               f"🎯 **هدف الـ 5%:** {data['target']}$")
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ لم أجد بيانات لهذا الرمز، تأكد من كتابته بشكل صحيح (مثلاً: TSLA)")

# 5. تشغيل البوت
if __name__ == '__main__':
    # تشغيل خادم الويب في الخلفية
    Thread(target=run).start()
    
    # تشغيل تليجرام
    if TOKEN:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("جاري بدء تشغيل البوت...")
        application.run_polling()
