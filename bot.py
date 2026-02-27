import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# قائمة أوسع تشمل أسهم تحت 20 و 50 دولار (SOFI, F, LCID, NIO, INTC, PLTR, AMC)
WATCHLIST = ["AAPL", "TSLA", "NVDA", "AMD", "PLTR", "SOFI", "LCID", "F", "NIO", "INTC", "AMC", "DKNG", "PFE", "GRAB", "T"]

def get_stock_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    # بحث عن الأخبار في آخر 48 ساعة لضمان وجود نتائج
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2026-02-25&to=2026-02-27&token={FINNHUB_API}"
    
    try:
        price_res = requests.get(quote_url).json()
        news_res = requests.get(news_url).json()
        
        current_price = price_res.get('c', 0)
        change_percent = price_res.get('dp', 0)
        
        sentiment = "محايد"
        news_headline = "No recent news"
        
        if news_res and len(news_res) > 0:
            news_headline = news_res[0]['headline']
            headline_lower = news_headline.lower()
            # كلمات مفتاحية أوسع للأخبار الإيجابية
            pos_keywords = ['up', 'growth', 'profit', 'buy', 'positive', 'success', 'beat', 'boost', 'raise', 'upgrade']
            if any(w in headline_lower for w in pos_keywords):
                sentiment = "إيجابي ✅"
        
        return current_price, change_percent, sentiment, news_headline
    except:
        return 0, 0, "خطأ", ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().split()
    if not user_input: return
    
    command = user_input[0]
    # قراءة السعر المطلوب بدقة
    try:
        max_p = float(user_input[1]) if len(user_input) > 1 else 999999
    except:
        max_p = 999999

    await update.message.reply_text(f"⏳ جاري فحص السوق لطلبك: ({command}) تحت سعر {max_p}$...")

    found = False
    for sym in WATCHLIST:
        price, mom, sent, news = get_stock_analysis(sym)
        
        if price > 0 and price <= max_p:
            if command == "زخم" and mom > 1.5: # خفضنا حد الزخم قليلاً لإيجاد نتائج أكثر
                msg = f"🔥 **زخم: {sym}**\n💰 السعر: {price}$\n📈 التغير: {mom}%\n📜 الخبر: {news}"
                await update.message.reply_text(msg)
                found = True
            elif command == "إيجابي" and sent == "إيجابي ✅":
                msg = f"✅ **إيجابي: {sym}**\n💰 السعر: {price}$\n📊 التقييم: {sent}\n📜 الخبر: {news}"
                await update.message.reply_text(msg)
                found = True

    if not found:
        await update.message.reply_text(f"⚠️ لم يتم العثور على نتائج تطابق ( {command} ) تحت سعر {max_p}$ حالياً.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
