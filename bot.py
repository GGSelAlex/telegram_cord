import os
from dotenv import load_dotenv
import telebot
from flask import Flask, request, jsonify

# =========================
# Ініціалізація
# =========================
load_dotenv()  # завантаження .env

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [
    int(os.getenv("ADMIN1_ID", "0")),
    int(os.getenv("ADMIN2_ID", "0"))
]

# =========================
# Послуги
# =========================
SERVICES = {
    "ВИЇЗД": {
        "text": "Білий квиток: Ваш Шлях до Свободи та Спокою\nВи отримуєте повну легальну підтримку для виїзду за кордон.",
        "docs": ["Тимчасове посвідчення", "ВЛК", "Довідка на право на виїзд"]
    },
    "ІНВАЛІДНІСТЬ": {
        "text": "Група Інвалідності: Ваше Право на Захист та Соціальні Гарантії",
        "docs": ["ВЛК", "Довідка ЕКОПФ (МСЕК)", "Право на пенсію"]
    },
    "ВІДТЕРМІНУВАННЯ": {
        "text": "Отстрочка на рік робиться протягом 3-5 днів по стану здоров'я (ВЛК). Можна пересуватися по Україні.",
        "docs": ["Тимчасове посвідчення", "Довідка (відтермінування на рік)", "ВЛК"]
    },
    "ЗВІЛЬНЕННЯ": {
        "text": "Індивідуальний підхід та повний юридичний супровід для звільнення з ЗСУ.",
        "docs": ["Пакет документів для звільнення", "ВЛК", "Рапорти та клопотання"]
    }
}

# =========================
# Flask сервер
# =========================
app = Flask(__name__)

def notify_admin(text):
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, text)

def send_service_details(chat_id, service_name):
    service = SERVICES[service_name]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💬 Консультація", url="https://t.me/uristcord"),
        telebot.types.InlineKeyboardButton(
            "💰 Оплата 1 USDT TRC20",
            url=f"https://your-payment-provider.com/pay?amount=1&currency=USDT_TRC&user_id={chat_id}"
        ),
        telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back")
    )
    doc_text = "\n".join([f"• {d}" for d in service["docs"]])
    full_text = f"*{service_name}*\n\n{service['text']}\n\n*Документи, які ви отримуєте:*\n{doc_text}"
    bot.send_message(chat_id, full_text, parse_mode="Markdown", reply_markup=markup)

# =========================
# Webhook
# =========================
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

# =========================
# IPN (підтвердження оплати)
# =========================
@app.route("/ipn", methods=["POST"])
def ipn():
    secret = request.headers.get("X-IPN-Secret")
    if secret != os.getenv("IPN_SECRET"):
        return jsonify({"status": "unauthorized"}), 403

    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")
    currency = data.get("currency")
    status = data.get("status")

    if status == "success" and user_id:
        bot.send_message(user_id, f"✅ Оплата {amount} {currency} підтверджена! Дякуємо за оплату.")
        notify_admin(f"Користувач {user_id} сплатив {amount} {currency}")
        return jsonify({"status": "ok"}), 200

    return jsonify({"status": "failed"}), 400

# =========================
# Команди
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")

    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)
    notify_admin(f"Новий користувач натиснув /start: {chat_id} ({message.from_user.first_name})")

# =========================
# Основні блоки
# =========================
@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services_handler(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("ВИЇЗД", "ВІДТЕРМІНУВАННЯ")
    markup.row("ІНВАЛІДНІСТЬ", "ЗВІЛЬНЕННЯ")
    markup.row("🔙 Назад")
    bot.send_message(
        message.chat.id,
        "Ми надаємо:\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in SERVICES.keys())
def service_handler(message):
    send_service_details(message.chat.id, message.text)

# =========================
# Callback “Назад”
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_handler(call):
    services_handler(call.message)

# =========================
# Запис на консультацію
# =========================
@bot.message_handler(func=lambda m: m.text == "🕒 Запис на консультацію")
def consult(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("Надіслати номер телефону", request_contact=True),
        telebot.types.KeyboardButton("💬 Написати юристу"),
        telebot.types.KeyboardButton("🔙 Назад")
    )
    bot.send_message(
        message.chat.id,
        "📞 Для запису на консультацію — залиште свій номер телефону або напишіть юристу:",
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    contact = message.contact.phone_number
    bot.send_message(message.chat.id, f"Дякуємо! Ми отримали ваш номер: {contact}")
    notify_admin(f"Користувач надіслав номер телефону: {contact} (ID: {message.chat.id})")

# =========================
# Запуск сервера
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
