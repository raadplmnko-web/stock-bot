import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# جلب المفاتيح من إعدادات Render
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

def analyze_stock_logic(symbol):
    # 1. جلب بيانات السعر والحجم
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    # 2. جلب الأخبار الحديثة
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    price_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    current_price = price_res.get('c', 0)
    change_percent = price_res.get('dp', 0) # نسبة التغير اليومي
    
    # تحديد حالة الزخم وقوة الشراء
    if change_percent > 2.5:
        momentum = "🔥 شراء عالي وزخم قوي جداً"
    elif 0 < change_percent <= 2.5:
        momentum = "📈 زخم صاعد متوسط"
    else:
        momentum = "📉 زخم منخفض / تصحيح"

    # تحليل تقييم الخبر باللغة العربية
    sentiment = "محايد ⚠️"
    headline_ar = "لا توجد أخبار حديثة"
    
    if news_res:
        headline = news_res[0]['headline']
        headline_ar = headline # يمكن دمج خدمة ترجمة هنا لاحقاً
        
        pos_keywords = ['up', 'growth', 'profit', 'buy', 'positive', 'success', 'beat', 'boost']
        neg_keywords = ['down', 'loss', 'sell', 'negative', 'drop', 'fail', 'risk', 'cut']
        
        lower_headline = headline.lower()
        if any(w in lower_headline for w in pos_keywords):
            sentiment = "إيجابي ✅"
        elif any(w in lower_headline for w in neg_keywords):
            sentiment = "سلبي ❌"

    # حساب النقاط الفنية
    entry = current_price
    stop_loss = round(current_price * 0.96, 2) # وقف خسارة 4%
    target = round(current_price * 1.06, 2)    # هدف 6%

    return current_price, momentum, sentiment, headline_ar, entry, stop_loss, target

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    current_time = datetime.now().strftime("%H:%M")
    
    try:
        price, momentum, sentiment, news, entry, stop, target = analyze_stock_logic(symbol)
        
        message = (
            f"⚡️ **رادار الزخم الذكي — {current_time}** 🇸🇦\n\n"
            f"🔶 **الرمز:** {symbol} 🇺🇸\n"
            f"📊 **حالة الزخم:** {momentum}\n"
            f"💰 **السعر الحالي:** {price} دولار\n"
            f"🔷 **تقييم الخبر:** {sentiment}\n\n"
            f"📰 **محتوى الخبر:**\n"
            f"{news}\n\n"
            f"🎯 **التحليل الفني:**\n"
            f"📥 **نقطة الدخول:** {entry}\n"
            f"🚫 **وقف الخسارة:** {stop}\n"
            f"🚀 **الهدف المتوقع:** {target}\n\n"
            f"⚠️ *تحليل آلي - قراراتك مسؤوليتك*"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ تأكد من رمز السهم (مثال: NVDA)")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
