 import os, requests, asyncio, pytz
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

# ================== Flask لإبقاء البوت حي ==================
app = Flask('')
@app.route('/')
def home(): return "Bot is alive and running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ================== المتغيرات ==================
TOKEN = os.getenv('TOKEN')
FINNHUB_API = os.getenv('FINNHUB_API')
CHAT_ID = os.getenv('CHAT_ID')

# ================== التحقق من وقت السوق الأمريكي ==================
def market_is_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5: return False
    open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now <= close_time

# ================== ترجمة الأخبار ==================
def translate_to_arabic(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q={text}"
        res = requests.get(url).json()
        return res[0][0][0]
    except: return "لا توجد تفاصيل إضافية"

# ================== التحليل الكامل ==================
def get_full_analysis(symbol):
    try:
        quote = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API}").json()
        profile = requests.get(f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API}").json()
        
        current_price = quote.get('c', 0)
        open_price = quote.get('o', 1)
        if current_price == 0: return None

        percent_change = ((current_price - open_price) / open_price) * 100
        industry = profile.get('finnhubIndustry', '').lower()
        sharia = "✅ مطابق" if not any(x in industry for x in ["bank", "finance", "insur", "bev"]) else "❌ غير مطابق"

        return {
            "symbol": symbol, "price": current_price, "percent_change": round(percent_change, 2),
            "target": round(current_price * 1.03, 2), "stop_loss": round(current_price * 0.985, 2), "sharia": sharia
        }
    except: return None

# ================== الرد على الرسائل ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().upper()
    data = get_full_analysis(text)
    if data:
        msg = (f"📊 **سهم: {text}**\n━━━━━━━━━━━━\n"
               f"💰 **السعر:** {data['price']}$\n📊 **التغير:** {data['percent_change']}%\n"
               f"🎯 **الهدف:** {data['target']}$\n🛑 **الوقف:** {data['stop_loss']}$\n"
               f"📜 **الشرعية:** {data['sharia']}")
        await update.message.reply_text(msg, parse_mode='Markdown')

# ================== الماسح التلقائي (طريقة Render المستقرة) ==================
async def daily_opportunities(application: Application):
    while True:
        try:
            if market_is_open() and CHAT_ID:
                # محاكاة البحث عن فرصة (مثال: AAPL)
                data = get_full_analysis("AAPL")
                if data:
                    message = f"🚀 **فرصة رادار الآن:**\nسهم {data['symbol']} بسعر {data['price']}$"
                    await application.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
        except Exception as e: print(f"Error in task: {e}")
        await asyncio.sleep(1800)

# ================== تشغيل البوت ==================
async def main():
    if not TOKEN: return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل الماسح في الخلفية بشكل صحيح
    asyncio.create_task(daily_opportunities(application))
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        while True: await asyncio.sleep(1)

if __name__ == '__main__':
    Thread(target=run).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
