# ariza_bot.py
import os
import json
import time
from datetime import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# ====== CONFIG ======
TOKEN = "8559876835:AAFeaYluA74t1op9Yq_lihf2C8uFxYvBekA"   # <-- Bu yerga bot tokeningizni qo'ying
ADMIN_ID = 8474592025            # <-- Bu yerga o'zingizning telegram id'ingizni qo'ying

STATS_FILE = "stats.json"
APPS_FILE = "applications.json"

# ====== LOGGING ======
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== STORAGE ======
stats = {"users": [], "menu_clicks": 0, "card_views": 0, "auto_ads": False}
applications = {"list": []}

if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        stats = json.load(f)
if os.path.exists(APPS_FILE):
    with open(APPS_FILE, "r", encoding="utf-8") as f:
        applications = json.load(f)

# ====== UTILS ======
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

# ====== KEYBOARDS ======
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Ariza topshirish", callback_data="apply_card")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])

# ====== CONVERSATION STATES ======
APPLY_NAME, APPLY_FAMILY, APPLY_PHONE, APPLY_PASSPORT, APPLY_CONFIRM = range(5)

# ====== HANDLERS ======
def start(update: Update, context):
    user = update.message.from_user
    user_id = user.id
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_json(STATS_FILE, stats)
    update.message.reply_text("Xush kelibsiz! Botni ishlatish uchun pastdagi tugmalardan tanlang:", reply_markup=main_menu())

def callback_button(update: Update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "apply_card":
        query.message.reply_text("📝 Ariza topshirishni boshlaymiz. Ismingizni kiriting:")
        return APPLY_NAME

    if data == "back":
        query.message.reply_text("Asosiy menyuga qaytdingiz:", reply_markup=main_menu())
        return ConversationHandler.END

    if data == "stats":
        txt = f"📊 Foydalanuvchilar soni: {len(stats['users'])}"
        query.message.reply_text(txt)
        return

# ====== APPLICATION ======
def apply_name(update: Update, context):
    context.user_data['app_name'] = update.message.text.strip()
    update.message.reply_text("Familiyangizni kiriting:")
    return APPLY_FAMILY

def apply_family(update: Update, context):
    context.user_data['app_family'] = update.message.text.strip()
    update.message.reply_text("Telefon raqamingizni kiriting (masalan +998901234567):")
    return APPLY_PHONE

def apply_phone(update: Update, context):
    context.user_data['app_phone'] = update.message.text.strip()
    update.message.reply_text("Passport seriya/raqamini kiriting:")
    return APPLY_PASSPORT

def apply_passport(update: Update, context):
    context.user_data['app_passport'] = update.message.text.strip()
    summary = f"Ism: {context.user_data['app_name']}\nFamiliya: {context.user_data['app_family']}\nTelefon: {context.user_data['app_phone']}\nPassport: {context.user_data['app_passport']}\n\nTasdiqlaysizmi? (ha / yo'q)"
    update.message.reply_text(summary)
    return APPLY_CONFIRM

def apply_confirm(update: Update, context):
    txt = update.message.text.strip().lower()
    if txt in ("ha","ok"):
        app = {
            "user_id": update.message.from_user.id,
            "name": context.user_data['app_name'],
            "family": context.user_data['app_family'],
            "phone": context.user_data['app_phone'],
            "passport": context.user_data['app_passport'],
            "time": datetime.utcnow().isoformat()
        }
        applications["list"].append(app)
        save_json(APPS_FILE, applications)
        update.message.reply_text("✅ Arizangiz qabul qilindi!", reply_markup=main_menu())
        # Adminga yuborish
        try:
            context.bot.send_message(chat_id=ADMIN_ID, text=f"Yangi ariza:\nID: {app['user_id']}\nIsm: {app['name']}\nFamiliya: {app['family']}\nTelefon: {app['phone']}\nPassport: {app['passport']}\nVaqti: {app['time']}")
        except:
            pass
        return ConversationHandler.END
    else:
        update.message.reply_text("Ariza bekor qilindi.", reply_markup=main_menu())
        return ConversationHandler.END

def apply_cancel(update: Update, context):
    update.message.reply_text("Ariza bekor qilindi.", reply_markup=main_menu())
    return ConversationHandler.END

# ====== MAIN ======
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_button)],
        states={
            APPLY_NAME: [MessageHandler(Filters.text & ~Filters.command, apply_name)],
            APPLY_FAMILY: [MessageHandler(Filters.text & ~Filters.command, apply_family)],
            APPLY_PHONE: [MessageHandler(Filters.text & ~Filters.command, apply_phone)],
            APPLY_PASSPORT: [MessageHandler(Filters.text & ~Filters.command, apply_passport)],
            APPLY_CONFIRM: [MessageHandler(Filters.text & ~Filters.command, apply_confirm)],
        },
        fallbacks=[CommandHandler('cancel', apply_cancel)],
        allow_reentry=True
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    print("Bot ishga tushdi. Polling ishlayapti.")
    updater.idle()

if __name__ == "__main__":
    main()

