
# bot_ptb20.py
import os
import json
import time
import threading
from datetime import datetime
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ========= CONFIG =========
TOKEN = os.environ.get("TOKEN")
 
ADMIN_ID = 123456789

STATS_FILE = "stats.json"

# ========= LOGGING =========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========= STORAGE =========
stats = {"users": [], "menu_clicks": 0, "card_views": 0, "auto_ads": False}
if os.path.exists(STATS_FILE):
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except:
        pass

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")  # Render-da environment variable sifatida TOKEN qo'shing
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))


# ========= KEYBOARDS =========
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💳 Uzcard + UnionPay", callback_data="uzcard")],
        [InlineKeyboardButton("💵 Dollar kursi", callback_data="dollar")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])


# ========= DOLLAR RATE =========
def get_usd_rate():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        data = requests.get(url, timeout=5).json()
        for item in data:
            if item['Ccy'] == 'USD':
                return f"💵 1 USD = {item['Rate']} so'm\n📅 Sana: {item['Date']}"
        return "USD kursini olishda muammo!"
    except:
        return "⚠ Dollar kursini olishda xatolik!"

# ========= HANDLERS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_stats()

# ========= HANDLERS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Kartalar ro‘yxatiga xush kelibsiz!", reply_markup=main_menu())

async def callback_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data


    stats["menu_clicks"] += 1
    save_stats()

    if data == "uzcard":
        stats["card_views"] += 1
        save_stats()
        await query.edit_message_text("💳 Uzcard + UnionPay\nNarxi: 40 000 so‘m\nMuddati: 3 yil", reply_markup=back_button())
    elif data == "dollar":
        rate = get_usd_rate()
        await query.edit_message_text(rate, reply_markup=back_button())
    elif data == "stats":
        text = f"📊 Statistika:\n👥 Foydalanuvchilar: {len(stats['users'])}\n📂 Menyu ochilgan: {stats['menu_clicks']} marta\n💳 Kartalar ko‘rilgan: {stats.get('card_views',0)} marta"
        await query.edit_message_text(text, reply_markup=back_button())
    elif data == "back":
        await query.edit_message_text("Kartalar ro‘yxatiga qaytdingiz.", reply_markup=main_menu())

# ========= MAIN =========
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_button))

    print("Bot ishga tushdi. Polling ishlayapti...")
    await app.run_polling()

import asyncio
asyncio.run(main())

    if data == "uzcard":
        await query.edit_message_text("💳 Uzcard + UnionPay\nNarxi: 40 000 so‘m\nMuddati: 3 yil", reply_markup=back_button())
    elif data == "dollar":
        await query.edit_message_text("💵 1 USD = 11 000 so‘m", reply_markup=back_button())  # demo kurs
    elif data == "stats":
        await query.edit_message_text("Statistika demo", reply_markup=back_button())
    elif data == "back":
        await query.edit_message_text("Kartalar ro‘yxatiga qaytdingiz.", reply_markup=main_menu())

# ========= APPLICATION =========
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback_button))

# ========= RENDERDA POLLING =========
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(app.run_polling())
    loop.run_forever()


