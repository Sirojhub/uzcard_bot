import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = "6837729821:AAHldyqE1OwM3-hEQTpjnkmNMThBHZkrvV0"

# Dollar kursini olish funksiyasi
def get_usd_rate():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/"
        data = requests.get(url).json()
        rate = data[0]["Rate"]
        date = data[0]["Date"]
        return f"💵 <b>1 USD = {rate} so'm</b>\n📅 Sana: {date}"
    except:
        return "❌ Kursni olishda xatolik yuz berdi."

# /start buyrug‘i
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💵 Dollar kursi", callback_data='kurs')],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "<b>Assalomu alaykum!</b>\n\n"
        "Bu bot sizga har doim eng so‘nggi dollar kursini taqdim etadi.\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# Tugmalarni bosganda ishlovchi funksiya
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'kurs':
        query.edit_message_text(get_usd_rate(), parse_mode='HTML')
    elif query.data == 'about':
        query.edit_message_text(
            "💡 <b>Dollar Kursi Bot</b>\n"
            "🖌 Dizayner tomonidan tayyorlangan professional menyu\n"
            "💵 Har doim eng so‘nggi kursni ko‘rsatadi\n"
            "🔄 /start tugmasi bilan bosh menyuga qaytishingiz mumkin",
            parse_mode='HTML'
        )

# Botni ishga tushirish
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

