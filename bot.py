import os
import requests
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- إعدادات الخادم لمنع النوم ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات البوت الأساسية ---
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
CHAT_ID = "687056332"

# قائمة الأسهم النشطة للمراقبة التلقائية
HOT_LIST = ["TSLA", "NVDA", "AAPL", "AMD", "PLTR", "SOFI", "LCID", "VEEA", "NIO", "INTC", "DKNG", "F"]

def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except: return text

def get_complete_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2026-02-25&to=2026-02-27&token={FINNHUB_API}"
    profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}"
    
    p_res = requests.get(quote_url).json()
    n_res = requests.get(news_url).json()
    prof_res = requests.get(profile_url).json()
    
    price = p_res.get('c', 0)
    change = p_res.get('dp', 0)
    if price == 0: return None

    # فلتر الشرعية (عوايد)
    industry = prof_res.get('finnhubIndustry', '').lower()
    prohibited = ['banking', 'financial services', 'beverages', 'entertainment', 'insurance']
    is_sharia = "✅ مطابق للشريعة (عوايد)" if not any(s in industry for s in prohibited) else "❌ غير شرعي"

    # تحليل الخبر
    sentiment = "محايد ⚠️"
    headline_ar = "لا توجد أخبار حديثة"
    if n_res:
        headline_en = n_res[0]['headline']
        headline_ar = translate_to_arabic(headline_en)
        if any(w in headline_en.lower() for w in ['up', 'growth', 'profit', 'beat', 'surge', 'positive']):
            sentiment = "إيجابي ✅"

    # حساب النقاط الفنية
    target = round(price * 1.07, 4)
    stop = round(price * 0.94, 4)

    return {
        "price": price, "change": change, "sharia": is_sharia,
        "sent": sentiment, "news": headline_ar, "target": target, "stop": stop
    }

# وظيفة التنبيه التلقائي كل 4 ساعات
async def auto_alert(context: ContextTypes.DEFAULT_TYPE):
    for sym in ["TSLA", "NVDA", "PLTR", "VEEA"]: # عينة للمراقبة التلقائية
        data = get_complete_analysis(sym)
        if data and data['change'] > 3.0: # إذا تحرك السهم أكثر من 3%
            msg = (f"🚨 **تنبيه رادار الزخم** 🚨\n\n"
                   f"السهم: {sym}\nالشرعية: {data['sharia']}\n"
                   f"السعر: {data['price']}$\nالارتفاع: {data['change']}%\n"
                   f"الخبر: {data['news']}")
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    wait_msg = await update.message.reply_text(f"🔍 فحص شامل لـ {symbol}...")
    
    data = get_complete_analysis(symbol)
    if not data:
        await wait_msg.edit_text("❌ الرمز غير صحيح.")
        return

    message = (
        f"📊 **تقرير السهم: {symbol}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📜 **الشرعية:** {data['sharia']}\n"
        f"💰 **السعر الحالي:** {data['price']}$\n"
        f"🔷 **التقييم:** {data['sent']}\n\n"
        f"📰 **الخبر:** {data['news']}\n\n"
        f"🎯 **خطة التداول:**\n"
        f"📥 **الدخول:** {data['price']}$\n"
        f"🚀 **الهدف:** {data['target']}$\n"
        f"🚫 **الوقف:** {data['stop']}$\n"
        f"━━━━━━━━━━━━━━━"
    )
    await wait_msg.edit_text(message, parse_mode='Markdown')

if __name__ == '__main__':
    keep_alive() # تشغيل خادم منع النوم
    application = Application.builder().token(TOKEN).build()
    
    # برمجة التنبيهات التلقائية
    job_queue = application.job_queue
    job_queue.run_repeating(auto_alert, interval=14400, first=10)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
