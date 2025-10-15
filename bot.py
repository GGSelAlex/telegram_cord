import telebot
import os
from telebot import types
from flask import Flask, request

# --- Токен та адміністратори з Environment Variables ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("ADMIN1_ID")), int(os.getenv("ADMIN2_ID"))]

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- Flask Webhook ---
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    return "Bot is running via webhook", 200

# --- Старт і привітання ---
@bot.message_handler(commands=['start'])
def start(message):
    # Привітальне повідомлення
    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

    # Сповіщення для адміністраторів
    admin_msg = f"Новий користувач: @{message.from_user.username or 'Немає username'}, ID: {message.from_user.id}"
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, admin_msg)

# --- Послуги ---
@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("ВИЇЗД", "ВІДТЕРМІНУВАННЯ")
    markup.row("ІНВАЛІДНІСТЬ", "ЗВІЛЬНЕННЯ")
    markup.row("⬅️ Назад")
    text = (
        "Ми надаємо:\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

# --- Деталі послуг ---
def service_details_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Консультація", url="https://t.me/uristcord"))
    markup.add(types.InlineKeyboardButton("Оплата USDT TRC20", url="https://your_payment_link_here"))
    return markup

@bot.message_handler(func=lambda m: m.text == "ВИЇЗД")
def service_vyezd(message):
    text = (
        "💳 *Виїзд за кордон*\n\n"
        "Білий квиток: Ваш шлях до свободи та спокою.\n"
        "Документи: Тимчасове посвідчення, ВЛК, Довідка на право виїзду."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=service_details_markup())

@bot.message_handler(func=lambda m: m.text == "ІНВАЛІДНІСТЬ")
def service_invalid(message):
    text = (
        "💳 *Інвалідність*\n\n"
        "Група інвалідності (ІІ або ІІІ) та соціальні гарантії.\n"
        "Документи: ЛЛК, довідка ЕКОПФ(МСЕК), право на пенсію."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=service_details_markup())

@bot.message_handler(func=lambda m: m.text == "ВІДТЕРМІНУВАННЯ")
def service_otst(message):
    text = (
        "💳 *Відтермінування*\n\n"
        "Отримання відтермінування на рік по стану здоров'я.\n"
        "Документи: Тимчасове посвідчення, Довідка (відтермінування на рік), ВЛК."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=service_details_markup())

@bot.message_handler(func=lambda m: m.text == "ЗВІЛЬНЕННЯ")
def service_release(message):
    text = (
        "💳 *Звільнення з ЗСУ*\n\n"
        "Індивідуальний підхід та юридичні гарантії.\n"
        "Документи: Офіційний договір та повний супровід."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=service_details_markup())

# --- Запис на консультацію ---
@bot.message_handler(func=lambda m: m.text == "🕒 Запис на консультацію")
def consult(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Надіслати номер телефону")
    markup.row("⬅️ Назад")
    markup.row("Написати юристу")
    bot.send_message(
        message.chat.id,
        "📞 Для запису на консультацію надішліть свій номер телефону або зв’яжіться з юристом:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Надіслати номер телефону")
def send_phone(message):
    bot.send_message(
        message.chat.id,
        "Натисніть кнопку нижче, щоб надіслати свій контакт:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton("Надіслати контакт", request_contact=True),
            types.KeyboardButton("⬅️ Назад")
        )
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        phone = message.contact.phone_number
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, f"Номер користувача: {phone}\nID: {message.from_user.id}")

@bot.message_handler(func=lambda m: m.text in ["⬅️ Назад", "Написати юристу"])
def go_back(message):
    start(message)

# --- Про компанію ---
@bot.message_handler(func=lambda m: m.text == "ℹ️ Про компанію")
def about(message):
    bot.send_message(
        message.chat.id,
        "Ми працюємо з 2022 року для підтримки та захисту чоловіків.\n"
        "Kovalova Legal — преміальний сервіс юридичної допомоги."
    )

# --- Контакти ---
@bot.message_handler(func=lambda m: m.text == "💬 Консультація")
def contact(message):
    bot.send_message(
        message.chat.id,
        "Натисніть, щоб написати юристу:\n👉 [Написати Ковалову](https://t.me/uristcord)",
        parse_mode="Markdown"
    )

# --- Запуск Flask ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
