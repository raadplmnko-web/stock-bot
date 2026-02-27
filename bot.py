import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# جلب المفاتيح من إعدادات Render
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# قائمة استرشادية للأسهم الشرعية (يمكنك إضافة أي سهم جديد هنا)
ISLAMIC_STOCKS = ["AAPL", "TSLA", "NVDA", "AMD", "PLTR", "SOFI", "LCID", "VEEA", "NIO", "INTC", "DKNG", "F"]

def get_complete_analysis(symbol):
    # 1. جلب بيانات السعر والحجم
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    # 2. جلب الأخبار لآخر يومين لضمان المصداقية
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2026-02-25&to=2026-02-27&token={FINNHUB_API}"
    
    price_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    current_price = price_res.get('c', 0)
    change_percent = price_res.get('dp', 0)
    
    # تحليل الشرعية
    sharia = "✅ مطابق للشريعة (حسب القائمة)" if symbol in ISLAMIC_STOCKS else "⚠️ غير مفحوص / راجع فلتر الشرعية"
    
    # تحليل الخبر
    sentiment = "محايد ⚠️"
    headline = "لا توجد أخبار حديثة قوية"
    if news_res:
        headline = news_res[0]['headline']
        h_lower = headline.lower()
        pos_keywords = ['up', 'growth', 'profit', 'buy', 'positive', 'success', 'beat', 'boost', 'surge', 'upgrade']
        if any(w in h_lower for w in pos_keywords):
            sentiment = "إيجابي ✅"

    # حساب النقاط الفنية (Entry, Target, Stop)
    # تم الضبط لثلاث خانات عشرية لتناسب أسهم السنتات
    if current_price > 0:
        entry = current_price
        target = round(current_price * 1.08, 3) # هدف ربح 8%
        stop_loss = round(current_price * 0.95, 3) # وقف خسارة 5%
    else:
        entry = target = stop_loss = 0

    return current_price, change_percent, sharia, sentiment, headline, entry, target, stop_loss

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    
    # استثناء الكلمات الوظيفية
    if symbol in ["اليوم", "زخم", "إيجابي"]:
        return

    try:
        price, mom, sharia, sent, news, entry, target, stop = get_complete_analysis(symbol)
        
        if price == 0:
            await update.message.reply_text(f"❌ لم يتم العثور على بيانات للرمز: {symbol}")
            return

        # تجميع كل المعلومات في رسالة واحدة احترافية
        message = (
            f"🚀 **تقرير التحليل الفني والشرعي: {symbol}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📜 **حالة الشرعية:** {sharia}\n"
            f"💰 **السعر الحالي:** {price}$\n"
            f"📈 **التغير اليومي:** {mom}%\n"
            f"🔷 **تقييم الخبر:** {sent}\n"
            f"📰 **أهم خبر:** _{news}_\n\n"
            f"🎯 **توصية التداول:**\n"
            f"📥 **نقطة الدخول:** {entry}$\n"
            f"🚀 **الهدف الأول:** {target}$\n"
            f"🚫 **وقف الخسارة:** {stop}$\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ *هذا تحليل آلي، تأكد قبل اتخاذ قرارك.*"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ حدث خطأ، يرجى التأكد من رمز السهم.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
