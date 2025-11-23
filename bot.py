from dotenv import load_dotenv
import os

# .env dagi TOKEN ni yuklash
load_dotenv()
TOKEN = os.getenv("TOKEN")  # <-- TOKEN faqat shu yerda bo‘ladi

import json
import time
import threading
from datetime import datetime
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    Filters
)

# ========== CONFIG ==========
ADMIN_ID = 8474592025

STATS_FILE = "stats.json"
APPS_FILE = "applications.json"

SPAM_LIMIT_COUNT = 5
SPAM_LIMIT_SECONDS = 60

AUTO_ADS_INTERVAL = 86400  # 24 soat

# ========== LOGGING ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== HELPERS ==========
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("JSON load error %s: %s", path, e)
            return default
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("JSON save error %s: %s", path, e)

# ========== STORAGE ==========
stats = load_json(STATS_FILE, {"users": [], "menu_clicks": 0, "card_views": 0, "auto_ads": False})
applications = load_json(APPS_FILE, {"list": []})

user_actions = {}

def allowed_action(user_id):
    now = time.time()
    arr = user_actions.get(user_id, [])
    arr = [t for t in arr if now - t <= SPAM_LIMIT_SECONDS]
    arr.append(now)
    user_actions[user_id] = arr
    if len(arr) > SPAM_LIMIT_COUNT:
        return False, len(arr)
    return True, len(arr)

# ========== CARDS ==========
cards_info = {
    "uzcard_unionpay": {"title":"💳 Uzcard + UnionPay","text":"1️⃣ Uzcard + UnionPay\nNarxi: 40 000 so‘m\nMuddati: 3 yil\nValyuta: So‘m","image":None},
    "humo_visa": {"title":"💳 Humo + Visa","text":"2️⃣ Humo + Visa\nNarxi: 61 800 so‘m\nMuddati: 5 yil\nValyuta: So‘m","image":None},
    "visa": {"title":"💳 Visa karta","text":"3️⃣ Visa karta\nNarxi: 25 000 so‘m\nValyuta: Faqat dollar tushadi","image":None},
    "uzcard_kids": {"title":"👶 Uzcard Kids karta","text":"4️⃣ Uzcard Kids karta\nBolalar uchun maxsus","image":None}
}
bank_branches = [
    {
        "name": "Termiz Filiali",
        "address": "Surxondaryo, Termiz shahar, Amir Temur ko‘chasi 12",
        "map": "https://maps.google.com/?q=Surxondaryo+Termiz+Amir+Temur+12"
    },
    {
        "name": "Denov Filiali",
        "address": "Surxondaryo, Denov shahar, Mustaqillik ko‘chasi 5",
        "map": "https://maps.google.com/?q=Surxondaryo+Denov+Mustaqillik+5"
    },
    {
        "name": "Qumqorgon Filiali",
        "address": "Surxondaryo, Qumqorgon tumani, Sho‘ro ko‘chasi 3",
        "map": "https://maps.google.com/?q=Surxondaryo+Qumqorgon+Shoro+3"
    },
    {
        "name": "Angor Filiali",
        "address": "Surxondaryo, Angor tumani, Bobur ko‘chasi 7",
        "map": "https://maps.google.com/?q=Surxondaryo+Angor+Bobur+7"
    },
    {
        "name": "Jarqo‘rgon Filiali",
        "address": "Surxondaryo, Jarqo‘rgon tumani, Mustaqillik ko‘chasi 10",
        "map": "https://maps.google.com/?q=Surxondaryo+Jarqorgon+Mustaqillik+10"
    }


]

# ========== KEYBOARS ==========
def main_menu():
    keyboard = [
           
        [InlineKeyboardButton("📱 cvv kodni olish video rolik", url="https://www.youtube.com/shorts/Gp7M6GbAwHQ?feature=share")],
        [InlineKeyboardButton(cards_info["uzcard_unionpay"]["title"], callback_data="uzcard_unionpay")],
        [InlineKeyboardButton(cards_info["humo_visa"]["title"], callback_data="humo_visa")],
        [InlineKeyboardButton(cards_info["visa"]["title"], callback_data="visa")],
        [InlineKeyboardButton(cards_info["uzcard_kids"]["title"], callback_data="uzcard_kids")],
        [InlineKeyboardButton("📍 Bank filiallari", callback_data="bank_branches")],
        # InlineKeyboardButton("📝 Karta ariza (/apply)", callback_data="apply_card")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("🤝 karta uchun ariza yuboring", url="https://t.me/ariza_bot2921_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])

def admin_menu_kb():
    keyboard = [
        [InlineKeyboardButton("👥 Obunachilar ro'yxati", callback_data="admin_users")],
        [InlineKeyboardButton("🗂 Arizalar ro'yxati", callback_data="admin_apps")],
        [InlineKeyboardButton("📤 Broadcast xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📢 Auto-reklama ON/OFF", callback_data="admin_toggle_ads")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== START ==========
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_json(STATS_FILE, stats)
    update.message.reply_text("Kartalar ro‘yxatiga xush kelibsiz! Birini tanlang:", reply_markup=main_menu())

# ========== CALLBACK HANDLER ==========
def callback_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    ok, cnt = allowed_action(user_id)
    if not ok:
        query.answer("Ko‘p bosdingiz — iltimos bir oz kuting.", show_alert=True)
        return

    query.answer()
    data = query.data
    stats["menu_clicks"] = stats.get("menu_clicks",0)+1
    save_json(STATS_FILE, stats)

    if data.startswith("admin_"):
        return

    if data in cards_info:
        stats["card_views"] = stats.get("card_views",0)+1
        save_json(STATS_FILE, stats)
        card = cards_info[data]
        try:
            if card["image"]:
                context.bot.send_photo(chat_id=query.message.chat_id, photo=card["image"], caption=card["text"], reply_markup=back_button())
                query.edit_message_text("✅ Ma'lumot yuborildi.", reply_markup=back_button())
            else:
                query.edit_message_text(card["text"], reply_markup=back_button())
        except:
            query.edit_message_text(card["text"], reply_markup=back_button())
        return

    if data=="back":
        try:
            query.edit_message_text("Kartalar ro‘yxatiga qaytdingiz. Birini tanlang:", reply_markup=main_menu())
        except:
            query.message.reply_text("Kartalar ro‘yxatiga qaytdingiz. Birini tanlang:", reply_markup=main_menu())
        return

    if data=="bank_branches":
        txt = "📍 *Bank filiallari:*\n\n"
        for b in bank_branches:
            txt += f"*{b['name']}*\n{b['address']}\n[Ko‘rish]({b['map']})\n\n"
        try:
            query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        except:
            query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    if data=="stats":
        txt = f"📊 *Bot statistikasi:*\n\n👥 Foydalanuvchilar: *{len(stats.get('users',[]))}*\n📂 Menyu ochilgan: *{stats.get('menu_clicks',0)} marta*\n💳 Kartalar ko‘rilgan: *{stats.get('card_views',0)} marta*\n📢 Auto-reklama: *{'ON' if stats.get('auto_ads') else 'OFF'}*"
        try:
            query.edit_message_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        except:
            query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    if data=="apply_card":
        try:
            query.edit_message_text("Karta arizasi uchun /apply buyrug'ini yuboring.", reply_markup=back_button())
        except:
            query.message.reply_text("Karta arizasi uchun /apply buyrug'ini yuboring.", reply_markup=back_button())
        return

# ========== APPLICATION ==========
APPLY_NAME, APPLY_FAMILY, APPLY_PHONE, APPLY_PASSPORT, APPLY_CONFIRM = range(5)

def apply_start(update: Update, context: CallbackContext):
    update.message.reply_text("📝 Karta arizasini to'ldirishni boshlaymiz.\nIltimos, ismingizni yozing:")
    return APPLY_NAME

def apply_name(update: Update, context: CallbackContext):
    context.user_data['app_name'] = update.message.text.strip()
    update.message.reply_text("Familiyangizni yozing:")
    return APPLY_FAMILY

def apply_family(update: Update, context: CallbackContext):
    context.user_data['app_family'] = update.message.text.strip()
    update.message.reply_text("Telefon raqamingizni kiriting (masalan +998901234567):")
    return APPLY_PHONE

def apply_phone(update: Update, context: CallbackContext):
    context.user_data['app_phone'] = update.message.text.strip()
    update.message.reply_text("Passport seriya/raqamini yozing:")
    return APPLY_PASSPORT

def apply_passport(update: Update, context: CallbackContext):
    context.user_data['app_passport'] = update.message.text.strip()
    summary = f"Ism: {context.user_data.get('app_name')}\nFamiliya: {context.user_data.get('app_family')}\nTelefon: {context.user_data.get('app_phone')}\nPassport: {context.user_data.get('app_passport')}\n\nTasdiqlaysizmi? (ha / yo'q)"
    update.message.reply_text(summary)
    return APPLY_CONFIRM

def apply_confirm(update: Update, context: CallbackContext):
    txt = update.message.text.strip().lower()
    if txt in ("ha","ok"):
        app = {"user_id": update.message.from_user.id,"name":context.user_data.get("app_name"),"family":context.user_data.get("app_family"),"phone":context.user_data.get("app_phone"),"passport":context.user_data.get("app_passport"),"time":datetime.utcnow().isoformat()}
        applications.setdefault("list",[]).append(app)
        save_json(APPS_FILE, applications)
        update.message.reply_text("✅ Arizangiz qabul qilindi!", reply_markup=main_menu())
        try:
            msg=f"🔔 Yangi ariza:\nID: {app['user_id']}\nIsm: {app['name']}\nFamiliya: {app['family']}\nTelefon: {app['phone']}\nPassport: {app['passport']}\nVaqti: {app['time']}"
            context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        except:
            pass
        return ConversationHandler.END
    else:
        update.message.reply_text("Ariza bekor qilindi.", reply_markup=main_menu())
        return ConversationHandler.END

def apply_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Ariza bekor qilindi.", reply_markup=main_menu())
    return ConversationHandler.END

# ========== ADMIN ==========
def is_admin(user_id):
    return user_id==ADMIN_ID

def admin_command(update: Update, context: CallbackContext):
    if not is_admin(update.message.from_user.id):
        update.message.reply_text("Siz admin emassiz.")
        return
    update.message.reply_text("Admin panel:", reply_markup=admin_menu_kb())

def admin_callback(update: Update, context: CallbackContext):
    query=update.callback_query
    user_id=query.from_user.id
    if not is_admin(user_id):
        query.answer("Siz admin emassiz.", show_alert=True)
        return
    query.answer()
    data=query.data
    if data=="admin_users":
        users=stats.get("users",[])
        text=f"👥 Obunachilar soni: {len(users)}\n\nIDs:\n"+"\n".join(str(u) for u in users[:200])
        query.edit_message_text(text)
    elif data=="admin_apps":
        apps=applications.get("list",[])
        if not apps:
            query.edit_message_text("Ariza yo'q.")
        else:
            lines=[]
            for a in apps[-50:]:
                lines.append(f"ID:{a['user_id']} | {a['name']} {a['family']} | {a['phone']} | {a['passport']} | {a['time']}")
            query.edit_message_text("🔔 So‘nggi arizalar:\n\n"+"\n".join(lines))
    elif data=="admin_toggle_ads":
        stats["auto_ads"]=not stats.get("auto_ads",False)
        save_json(STATS_FILE, stats)
        query.edit_message_text(f"Auto-reklama: {'ON' if stats['auto_ads'] else 'OFF'}")
    elif data=="back":
        query.edit_message_text("Admin paneldan chiqildi.")
    else:
        query.edit_message_text("Noma'lum amr.")

def admin_text_handler(update: Update, context: CallbackContext):
    user_id=update.message.from_user.id
    if not is_admin(user_id):
        return
    if context.user_data.get('awaiting_broadcast'):
        text=update.message.text
        context.user_data['awaiting_broadcast']=False
        users=stats.get("users",[])
        sent=0
        for uid in users:
            try:
                context.bot.send_message(chat_id=uid, text=text)
                sent+=1
            except:
                pass
        update.message.reply_text(f"Xabar yuborildi: {sent} ta foydalanuvchiga.")

# ========== AUTO-ADS ==========
def auto_ads_worker(updater_obj):
    if stats.get("auto_ads"):
        text="📢 Auto reklama: Bizning xizmatlardan foydalaning!"
        users=stats.get("users",[])
        for uid in users:
            try:
                updater_obj.bot.send_message(chat_id=uid, text=text)
            except Exception:
                # xatolik yuz bersa shunchaki o‘tkazib yuboramiz
                pass
# ========== MAIN / BOT START ==========

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # /start handler
    dp.add_handler(CommandHandler("start", start))

    # Callback handler
    dp.add_handler(CallbackQueryHandler(callback_button))

    # Conversation handler for /apply
    apply_conv = ConversationHandler(
        entry_points=[CommandHandler('apply', apply_start)],
        states={
            APPLY_NAME: [MessageHandler(Filters.text & ~Filters.command, apply_name)],
            APPLY_FAMILY: [MessageHandler(Filters.text & ~Filters.command, apply_family)],
            APPLY_PHONE: [MessageHandler(Filters.text & ~Filters.command, apply_phone)],
            APPLY_PASSPORT: [MessageHandler(Filters.text & ~Filters.command, apply_passport)],
            APPLY_CONFIRM: [MessageHandler(Filters.text & ~Filters.command, apply_confirm)],
        },
        fallbacks=[CommandHandler('cancel', apply_cancel)]
    )
    dp.add_handler(apply_conv)

    # Admin handlers
    dp.add_handler(CommandHandler('admin', admin_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, admin_text_handler))
    dp.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # Start auto-ads thread
    def auto_ads_loop():
        while True:
            auto_ads_worker(updater)
            time.sleep(AUTO_ADS_INTERVAL)

    t = threading.Thread(target=auto_ads_loop, daemon=True)
    t.start()

    # Start polling
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()


