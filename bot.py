import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
CHAT_ID = "ضع_هنا_رقم_حسابك" # استبدل هذا الرقم برقم حسابك في تليجرام

# قائمة مراقبة واسعة للبحث التلقائي
HOT_LIST = ["TSLA", "NVDA", "AAPL", "AMD", "PLTR", "SOFI", "LCID", "VEEA", "NIO", "INTC", "DKNG", "F", "RIVN", "MARA"]

def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except: return text

def get_quick_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2026-02-26&to=2026-02-27&token={FINNHUB_API}"
    profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}"
    
    p_res = requests.get(quote_url).json()
    n_res = requests.get(news_url).json()
    prof_res = requests.get(profile_url).json()
    
    price = p_res.get('c', 0)
    change = p_res.get('dp', 0)
    industry = prof_res.get('finnhubIndustry', '').lower()
    
    # فلتر الشرعية
    prohibited = ['banking', 'financial services', 'beverages', 'entertainment', 'insurance']
    is_sharia = not any(s in industry for s in prohibited)
    
    score = 0
    headline_ar = ""
    if is_sharia and n_res:
        headline_en = n_res[0]['headline']
        headline_ar = translate_to_arabic(headline_en)
        # نظام نقاط لترشيح الأفضل
        if any(w in headline_en.lower() for w in ['beat', 'surge', 'buy', 'positive', 'growth']):
            score += 10
        score += change # إضافة نسبة التغيير كعامل زخم

    return {"sym": symbol, "price": price, "score": score, "news": headline_ar, "change": change}

# وظيفة التنبيه التلقائي (تعمل في الخلفية)
async def daily_alert(context: ContextTypes.DEFAULT_TYPE):
    results = []
    for sym in HOT_LIST:
        data = get_quick_analysis(sym)
        if data['score'] > 0:
            results.append(data)
    
    # ترتيب واختيار أفضل 3
    top_3 = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
    
    if top_3:
        msg = "🔔 **تنبيه الافتتاح: أقوى 3 فرص شرعية** 🚀\n━━━━━━━━━━━━━━━\n"
        for i, s in enumerate(top_3, 1):
            msg += f"{i}. **{s['sym']}**\n💰 السعر: {s['price']}$\n📈 الزخم: {s['change']}%\n📰 الخبر: _{s['news']}_\n\n"
        msg += "⚠️ *افحص النقاط الفنية قبل الدخول*"
        await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # (نفس كود التحليل الفردي السابق)
    symbol = update.message.text.upper().strip()
    # ... بقية المنطق ...

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    
    # برمجة التنبيه ليعمل تلقائياً كل 4 ساعات (أو وقت الافتتاح)
    job_queue = application.job_queue
    job_queue.run_repeating(daily_alert, interval=14400, first=10)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
