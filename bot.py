import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

# قائمة أمثلة لأسهم تُصنف غالباً كشرعية (يجب مراجعتها دورياً)
ISLAMIC_STOCKS = ["AAPL", "TSLA", "NVDA", "AMD", "PLTR", "SOFI", "LCID", "META", "AMZN", "GOOGL", "VEEA"]

def get_stock_analysis(symbol):
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    price_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    current_price = price_res.get('c', 0)
    change_percent = price_res.get('dp', 0)
    
    # تحديد الشرعية بناءً على القائمة
    sharia_status = "✅ مطابق للشريعة (حسب القائمة)" if symbol in ISLAMIC_STOCKS else "⚠️ غير مفحوص / راجع الفلتر"
    
    sentiment = "محايد"
    if news_res:
        headline = news_res[0]['headline'].lower()
        pos_keywords = ['up', 'growth', 'profit', 'buy', 'positive', 'success', 'beat']
        if any(w in headline for w in pos_keywords):
            sentiment = "إيجابي ✅"
            
    return current_price, change_percent, sentiment, sharia_status

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().split()
    command = text[0]
    
    try:
        max_price = float(text[1]) if len(text) > 1 else 999999
    except:
        max_price = 999999

    if command == "زخم":
        await update.message.reply_text(f"🚀 رادار الزخم (تحت {max_price}$)...")
        for sym in ISLAMIC_STOCKS: # سيبحث فقط في الأسهم الشرعية لراحتك
            price, mom, sent, sharia = get_stock_analysis(sym)
            if mom > 2.0 and price <= max_price:
                msg = (f"🔥 **سهم شرعي عليه زخم: {sym}**\n"
                       f"💰 السعر: {price}$\n"
                       f"📈 التغير: {mom}%\n"
                       f"📜 الحالة: {sharia}")
                await update.message.reply_text(msg)

    elif command == "إيجابي":
        await update.message.reply_text(f"🔍 أخبار إيجابية لأسهم شرعية (تحت {max_price}$)...")
        for sym in ISLAMIC_STOCKS:
            price, mom, sent, sharia = get_stock_analysis(sym)
            if sent == "إيجابي ✅" and price <= max_price:
                msg = (f"✅ **سهم شرعي إيجابي: {sym}**\n"
                       f"💰 السعر: {price}$\n"
                       f"📜 الحالة: {sharia}")
                await update.message.reply_text(msg)
    
    else:
        symbol = command.upper()
        try:
            price, mom, sent, sharia = get_stock_analysis(symbol)
            await update.message.reply_text(f"📊 **تحليل {symbol}**\n💰 السعر: {price}$\n📜 الشرعية: {sharia}")
        except:
            await update.message.reply_text("استخدم: زخم 20 أو إيجابي 100")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()
