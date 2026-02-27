import os, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. خادم الويب (لضمان بقاء البوت حياً) ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بكفاءة!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. جلب مفاتيح التشغيل ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# --- 3. وظيفة التحليل الفوري ---
def get_stock_analysis(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
        data = requests.get(url).json()
        price = data.get('c', 0)
        if price == 0: return None
        
        # حساب بسيط للهدف
        target = round(price * 1.05, 2)
        change = data.get('d', 0)
        status = "🟢 صاعد" if change > 0 else "🔴 هابط"
        
        return {
            "price": price,
            "status": status,
            "target": target
        }
    except: return None

# --- 4. معالج الرسائل في تليجرام ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    symbol = update.message.text.strip().upper()
    analysis = get_stock_analysis(symbol)
    
    if analysis:
        res = (f"🍎 **سهم: {symbol}**\n"
               f"━━━━━━━━━━━━\n"
               f"💰 **السعر الحالي:** {analysis['price']}$\n"
               f"📊 **حالة السوق:** {analysis['status']}\n"
               f"🎯 **هدف الـ 5% القادم:** {analysis['target']}$")
        await update.message.reply_text(res, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ تأكد من رمز السهم (مثال: AAPL)")

# --- 5. تشغيل النظام ---
if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل
    Thread(target=run).start()
    
    # تشغيل البوت
    if TOKEN:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("انطلق البوت!")
        application.run_polling()
