import telebot
import os
from flask import Flask, request

# === 1. Токен та список адмінів ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [8411342070, 8208162262]  # <- встав свої Telegram ID

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

# === 3. Функція сповіщення адміністраторів ===
def notify_admins(message_text):
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, message_text)

# === 4. /start ===
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id

    # Сповіщення всім адміністраторам
    notify_admins(f"🚀 Новий користувач натиснув /start:\nІм'я: {user_name}\nTelegram ID: {user_id}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")

    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# === 5. Послуги ===
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

# === 6. Запис на консультацію ===
@bot.message_handler(func=lambda m: m.text == "🕒 Запис на консультацію")
def consult(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_btn = telebot.types.KeyboardButton("Надіслати номер телефону", request_contact=True)
    write_btn = telebot.types.KeyboardButton("Написати юристу")
    markup.add(contact_btn, write_btn)
    bot.send_message(
        message.chat.id,
        "📞 Будь ласка, надішліть свій номер телефону для консультації або оберіть 'Написати юристу', якщо не хочете надсилати номер:",
        reply_markup=markup
    )

# === 7. Обробка контакту ===
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact.phone_number
    user_name = message.from_user.full_name
    user_id = message.from_user.id

    bot.send_message(
        message.chat.id,
        f"Дякуємо! Ваш номер {contact} отримано.\n"
        "Натисніть, щоб одразу написати юристу 👇",
        reply_markup=contact_markup()
    )

    notify_admins(f"📞 Новий контакт користувача:\nІм'я: {user_name}\nTelegram ID: {user_id}\nТелефон: {contact}")

# === 8. Кнопка "Написати юристу" ===
@bot.message_handler(func=lambda m: m.text == "Написати юристу" or m.text == "💬 Консультація")
def write_lawyer(message):
    bot.send_message(
        message.chat.id,
        "Натисніть, щоб одразу написати юристу:\n👉 [Написати Ковалову](https://t.me/uristcord)",
        parse_mode="Markdown",
        reply_markup=None
    )

# === 9. Про компанію ===
@bot.message_handler(func=lambda m: m.text == "ℹ️ Про компанію")
def about(message):
    bot.send_message(
        message.chat.id,
        "Ми працюємо з 2022 року заради підтримки та захисту чоловіків.\n"
        "Kovalova Legal — преміальний сервіс, який забезпечує юридичну "
        "допомогу у питаннях військової служби, соціального захисту та законності."
    )

# === 10. Inline кнопка для контакту з юристом ===
def contact_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Написати юристу", url="https://t.me/uristcord"))
    return markup

# === 11. Запуск Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
