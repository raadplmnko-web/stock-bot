import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# جلب المفاتيح من إعدادات Render
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')

def get_stock_data(symbol):
    # جلب سعر السهم
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}"
    # جلب أخبار السهم
    news_url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2024-01-01&to=2026-02-27&token={FINNHUB_API}"
    
    quote_res = requests.get(quote_url).json()
    news_res = requests.get(news_url).json()
    
    price = quote_res.get('c', 0)
    news_summary = news_res[0]['headline'] if news_res else "لا توجد أخبار حديثة"
    
    return price, news_summary

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في بوت الزخم ⚡️. أرسل رمز السهم (مثلاً: TSLA) للحصول على التقرير.")

async def send_stock_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper()
    current_time = datetime.now().strftime("%H:%M")
    
    try:
        price, news = get_stock_data(symbol)
        
        # تنسيق الرسالة لتبدو مثل الصورة تماماً
        message_text = (
            f"⚡️ **زخم بوت — {current_time}** 🇸🇦\n\n"
            f"🔶 الرمز <- {symbol} 🇺🇸\n"
            f"📋 نوع الحركة <- زخم صاعد\n"
            f"💰 السعر <- {price} دولار\n"
            f"🔷 يوجد خبر\n"
            f"📰 **محتوى الخبر:**\n"
            f"{news}"
        )
        
        await update.message.reply_text(message_text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("حدث خطأ، تأكد من رمز السهم أو مفتاح API.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    import telegram.ext
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.TEXT & ~telegram.ext.filters.COMMAND, send_stock_report))
    application.run_polling()
