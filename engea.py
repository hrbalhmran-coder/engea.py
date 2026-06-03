import os
import sys
import subprocess

# خدعة برمجية لتثبيت مكتبة تليجرام تلقائياً داخل سيرفر Render دون الحاجة لملف requirements.txt
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot"])
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes

import logging
import json
import urllib.request

# تم ربط التوكن الجديد ومفتاح جيمناي الجديد الخاص بك هنا مباشرة
BOT_TOKEN = os.getenv('BOT_TOKEN', '8521108982:AAHC_ykEAFjfk72Cz8mp7GGPf_l9zZyKcU0')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AQ.Ab8RN6K0VkVsNNHF7fJT5IaVxyvxra7OEobWvkFfliGkI9Sn3A')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة الربط المباشر بين البوت وبيني (Gemini AI)
def get_ai_response(user_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    data = {"contents": [{"parts": [{"text": f"أنت مهندس تصميم داخلي خبير، أجب بوضوح واحترافية: {user_text}"}]}]}
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

# حالات المحادثة للبوت
CHOOSING, AI_TUTOR, CALCULATOR_TYPE, CALCULATOR_CALC = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🧠 المساعد الذكي", callback_data='ai_tutor')],
        [InlineKeyboardButton("📐 الحاسبة الهندسية", callback_data='calc_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('أهلاً بك يا مهندس! اختر الخدمة:', reply_markup=reply_markup)
    return CHOOSING

async def handle_ai_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = await update.message.reply_text("⏳ جاري التحليل...")
    try:
        response_text = get_ai_response(update.message.text)
        await msg.edit_text(response_text)
    except:
        await msg.edit_text("حدث خطأ في الاتصال بالسيرفر.")
    return AI_TUTOR

async def calc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("🧱 بلاط", callback_data='tiles'), InlineKeyboardButton("🎨 طلاء", callback_data='paint')],
        [InlineKeyboardButton("💡 إضاءة", callback_data='light'), InlineKeyboardButton("🔙 عودة", callback_data='back')]
    ]
    await update.callback_query.edit_message_text("اختر نوع الحساب:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CALCULATOR_TYPE

async def handle_calc_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['calc_type'] = update.callback_query.data
    await update.callback_query.edit_message_text("أدخل الطول والعرض (مثال: 4 5):")
    return CALCULATOR_CALC

async def perform_calc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        l, w = map(float, update.message.text.split())
        area = l * w
        c_type = context.user_data.get('calc_type')
        if c_type == 'tiles': res = f"🧱 البلاط المطلوب (مع هدر 10%): {area * 1.1:.2f} م²"
        elif c_type == 'paint': res = f"🎨 الطلاء المطلوب (للوجهين): {area * 0.2:.2f} لتر"
        else: res = f"💡 الإضاءة المطلوبة: {area * 200:.0f} لومن"
        await update.message.reply_text(res)
    except:
        await update.message.reply_text("خطأ في البيانات. أرسل رقمين فقط مفصولين بمسافة.")
    return CHOOSING

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(calc_menu, pattern='calc_menu'), CallbackQueryHandler(lambda u,c: AI_TUTOR, pattern='ai_tutor')],
            AI_TUTOR: [MessageHandler(filters.TEXT, handle_ai_request)],
            CALCULATOR_TYPE: [CallbackQueryHandler(handle_calc_input, pattern='^(tiles|paint|light)$')],
            CALCULATOR_CALC: [MessageHandler(filters.TEXT, perform_calc)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv)
    print("🚀 البوت المحدث يعمل الآن وجاهز للاستضافة والاتصال بـ Gemini...")
    app.run_polling()
