import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

def analyze_sentiment(headline):
    # تحليل بسيط للخبر (يمكن تطويره بربطه بـ ChatGPT لاحقاً)
    positive_words = ['up', 'buy', 'growth', 'profit', 'positive', 'success', 'high']
    negative_words = ['down', 'sell', 'loss', 'negative', 'drop', 'low', 'risk']
    
    headline_low = headline.lower()
    if any(word in headline_low for word in positive_words):
        return "إيجابي ✅"
    elif any(word in headline_low for word in negative_words):
        return "سلبي ❌"
    else:
        return "محايد ⚠️"

def get_full_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    price_data = requests.get(quote_url).json()
    news_data = requests.get(news_url).json()
    
    current_price = price_data.get('c', 0)
    
    # حساب النقاط الفنية (مثال تقريبي)
    entry_point = current_price  # الدخول عند السعر الحالي
    stop_loss = round(current_price * 0.97, 2)  # وقف الخسارة عند 3%
    target_price = round(current_price * 1.05, 2)  # الهدف عند 5%
    
    headline = news_data[0]['headline'] if news_data else "لا توجد أخبار"
    sentiment = analyze_sentiment(headline) if news_data else "لا يوجد"
    
    return current_price, sentiment, headline, entry_point, stop_loss, target_price

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper()
    try:
        price, sentiment, news, entry, stop, target = get_full_analysis(symbol)
        
        message = (
            f"⚡️ **تحليل بوت الزخم — {symbol}** 🇸🇦\n\n"
            f"💰 **السعر الحالي:** {price} دولار\n"
            f"📊 **تقييم الخبر:** {sentiment}\n"
            f"📰 **الخبر:** {news}\n\n"
            f"🎯 **توصية فنية تقريبية:**\n"
            f"📥 **منطقة الدخول:** {entry}\n"
            f"🚫 **وقف الخسارة:** {stop}\n"
            f"🚀 **الهدف المتوقع:** {target}\n\n"
            f"⚠️ *هذا تحليل آلي وليس نصيحة مالية*"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ رمز السهم غير صحيح أو هناك مشكلة في البيانات.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
    
