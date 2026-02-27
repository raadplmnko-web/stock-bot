import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# قائمة الأسهم التي سيراقبها البوت عند البحث السريع
WATCHLIST = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "AMZN", "META", "GOOGL"]

def get_stock_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    price_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    current_price = price_res.get('c', 0)
    change_percent = price_res.get('dp', 0)
    
    sentiment = "محايد ⚠️"
    is_positive = False
    headline_en = "No news"
    
    if news_res:
        headline_en = news_res[0]['headline']
        pos_keywords = ['up', 'growth', 'profit', 'buy', 'positive', 'success', 'beat', 'boost']
        if any(w in headline_en.lower() for w in pos_keywords):
            sentiment = "إيجابي ✅"
            is_positive = True
            
    momentum_score = change_percent
    return current_price, momentum_score, sentiment, headline_en

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # حالة 1: طلب الأسهم ذات الأخبار الإيجابية
    if text == "إيجابي":
        await update.message.reply_text("🔍 جاري البحث عن أسهم بأخبار إيجابية...")
        found = False
        for sym in WATCHLIST:
            price, mom, sent, news = get_stock_analysis(sym)
            if sent == "إيجابي ✅":
                msg = f"✅ **سهم إيجابي: {sym}**\n💰 السعر: {price}\n📰 الخبر: _{news}_"
                await update.message.reply_text(msg, parse_mode='Markdown')
                found = True
        if not found: await update.message.reply_text("لا توجد أسهم بأخبار إيجابية حالياً في القائمة.")

    # حالة 2: طلب أسهم الزخم
    elif text == "زخم":
        await update.message.reply_text("🔥 جاري البحث عن أسهم الزخم (شراء عالي)...")
        found = False
        for sym in WATCHLIST:
            price, mom, sent, news = get_stock_analysis(sym)
            if mom > 2.0: # إذا كان الارتفاع أكثر من 2%
                msg = f"🔥 **زخم قوي: {sym}**\n📈 الارتفاع: {mom}%\n💰 السعر: {price}"
                await update.message.reply_text(msg, parse_mode='Markdown')
                found = True
        if not found: await update.message.reply_text("لا يوجد زخم قوي حالياً في القائمة.")

    # حالة 3: إرسال رمز سهم محدد
    else:
        symbol = text.upper()
        try:
            price, mom, sent, news = get_stock_analysis(symbol)
            message = (
                f"⚡️ **تحليل {symbol}**\n"
                f"📊 الزخم: {'🔥 قوي' if mom > 2 else '📉 هادئ'} ({mom}%)\n"
                f"💰 السعر: {price}\n"
                f"🔷 التقييم: {sent}\n"
                f"📰 الخبر: _{news}_"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
        except:
            await update.message.reply_text("أرسل رمز السهم أو كلمة (زخم) أو (إيجابي).")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
