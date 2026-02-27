import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

def analyze_stock(symbol):
    # 1. جلب بيانات السعر والحجم (الزخم)
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    # 2. جلب الأخبار
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    price_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    current_price = price_res.get('c', 0)
    change_percent = price_res.get('dp', 0)
    
    # تحديد حالة الزخم بناءً على نسبة التغير اليومي (مثال: أكثر من 2% يعتبر زخم صاعد)
    momentum_status = "🔥 شراء عالي وزخم قوي" if change_percent > 2 else "📉 زخم منخفض / مستقر"
    
    # تحليل الخبر وترجمته للعربية بشكل مبسط
    if news_res:
        headline = news_res[0]['headline']
        # تحليل المشاعر (Sentiment) - فحص كلمات مفتاحية
        pos_words = ['up', 'growth', 'profit', 'buy', 'positive', 'win']
        neg_words = ['down', 'loss', 'sell', 'negative', 'risk', 'fail']
        
        headline_lower = headline.lower()
        if any(w in headline_lower for w in pos_words):
            sentiment = "إيجابي ✅"
        elif any(w in headline_lower for w in neg_words):
            sentiment = "سلبي ❌"
        else:
            sentiment = "محايد ⚠️"
        news_content = headline
    else:
        sentiment = "لا يوجد أخبار"
        news_content = "لا توجد أخبار حديثة لهذا السهم."

    return current_price, momentum_status, sentiment, news_content

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper()
    try:
        price, momentum, sentiment, news = analyze_stock(symbol)
        current_time = datetime.now().strftime("%H:%M")
        
        message = (
            f"⚡️ **تقرير الزخم الذكي — {current_time}** 🇸🇦\n\n"
            f"🔶 الرمز <- {symbol} 🇺🇸\n"
            f"📋 حالة الزخم <- {momentum}\n"
            f"💰 السعر الحالي <- {price} دولار\n"
            f"🔷 تقييم الخبر <- {sentiment}\n\n"
            f"📰 **محتوى الخبر:**\n"
            f"{news}\n\n"
            f"📥 **نصيحة الدخول:** يفضل الدخول عند الاختراقات فقط."
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except:
        await update.message.reply_text("❌ لم يتم العثور على بيانات لهذا الرمز. تأكد من كتابته بشكل صحيح (مثال: TSLA).")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
