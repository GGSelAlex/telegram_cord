import telebot
import os
from flask import Flask, request

# === 1. Отримуємо токен з Render Environment ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8208162262  # <- заміни на свій Telegram ID

bot = telebot.TeleBot(TOKEN)

# === 2. Flask-сервер для Webhook ===
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    return "Bot is running via webhook", 200

# === 3. Кнопки для користувача ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")
    
    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services(message):
    bot.send_message(
        message.chat.id,
        "Ми надаємо:\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ\n\n"
        "Для запису скористайтесь кнопкою '🕒 Запис на консультацію'."
    )

@bot.message_handler(func=lambda m: m.text == "🕒 Запис на консультацію")
def consult(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = telebot.types.KeyboardButton("Надіслати номер телефону", request_contact=True)
    markup.add(button)
    bot.send_message(
        message.chat.id,
        "📞 Будь ласка, надішліть свій номер телефону для консультації або натисніть кнопку нижче:",
        reply_markup=markup
    )

# === 4. Обробка отриманого контакту ===
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact.phone_number
    user_name = message.from_user.full_name
    user_id = message.from_user.id

    # Відповідь користувачу
    bot.send_message(
        message.chat.id,
        f"Дякуємо! Ваш номер {contact} отримано.\n"
        "Натисніть, щоб одразу написати юристу 👇",
        reply_markup=contact_markup()
    )

    # Сповіщення адміну
    bot.send_message(
        ADMIN_ID,
        f"📞 Новий користувач:\n"
        f"Ім'я: {user_name}\n"
        f"Telegram ID: {user_id}\n"
        f"Телефон: {contact}"
    )

def contact_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Написати юристу", url="https://t.me/uristcord"))
    return markup

@bot.message_handler(func=lambda m: m.text == "ℹ️ Про компанію")
def about(message):
    bot.send_message(
        message.chat.id,
        "Ми працюємо з 2022 року заради підтримки та захисту чоловіків.\n"
        "Kovalova Legal — преміальний сервіс, який забезпечує юридичну "
        "допомогу у питаннях військової служби, соціального захисту та законності."
    )

@bot.message_handler(func=lambda m: m.text == "💬 Консультація")
def contact(message):
    bot.send_message(
        message.chat.id,
        "Натисніть, щоб одразу написати юристу:\n👉 [Написати Ковалову](https://t.me/uristcord)",
        parse_mode="Markdown"
    )

# === 5. Запуск Flask-сервера ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
