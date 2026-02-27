import os
import requests
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. إعداد خادم ويب بسيط لمنع النوم ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    # Render يتطلب الاستماع على المنفذ 10000 أو المنفذ المحدد في البيئة
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات البوت ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
CHAT_ID = "687056332"

def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except Exception:
        return text

def get_stock_analysis(symbol):
    try:
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
        profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}"
        
        p_res = requests.get(quote_url).json()
        prof_res = requests.get(profile_url).json()
        
        price = p_res.get('c', 0)
        if price == 0: return None

        # فلتر الشرعية المبسط
        industry = prof_res.get('finnhubIndustry', '').lower()
        prohibited = ['banking', 'financial services', 'beverages', 'insurance']
        is_sharia = "✅ مطابق للشريعة" if not any(s in industry for s in prohibited) else "❌ غير شرعي"

        return {"price": price, "sharia": is_sharia}
    except Exception:
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    symbol = update.message.text.upper().strip()
    wait_msg = await update.message.reply_text(f"🔍 فحص {symbol}...")
    
    data = get_stock_analysis(symbol)
    if not data:
        await wait_msg.edit_text("❌ رمز السهم غير صحيح أو لا توجد بيانات.")
        return

    message = (f"📊 **تحليل سهم: {symbol}**\n"
               f"━━━━━━━━━━━━\n"
               f"📜 **الشرعية:** {data['sharia']}\n"
               f"💰 **السعر الحالي:** {data['price']}$\n"
               f"🚀 **الهدف المتوقع:** {round(data['price']*1.07, 2)}$\n"
               f"🚫 **وقف الخسارة:** {round(data['price']*0.94, 2)}$\n"
               f"━━━━━━━━━━━━")
    await wait_msg.edit_text(message, parse_mode='Markdown')

# --- 3. تشغيل البوت ---
if __name__ == '__main__':
    # تشغيل خادم منع النوم أولاً
    keep_alive()
    
    # بناء وتطبيق البوت
    if TOKEN:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.run_polling()
    else:
        print("Error: No TOKEN found in environment variables.")
