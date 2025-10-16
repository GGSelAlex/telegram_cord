import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import telebot

# =========================
# Завантаження .env
# =========================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [
    int(os.getenv("ADMIN1_ID", "0")),
    int(os.getenv("ADMIN2_ID", "0"))
]

NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
IPN_SECRET = os.getenv("IPN_SECRET")

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
        "text": "Отстрочка на рік робимо протягом 3-5 днів по стану здоров'я (ВЛК). Можна пересуватися по Україні.",
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
        telebot.types.InlineKeyboardButton("💰 Оплата 1 USDT", callback_data="pay_usdt"),
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
# IPN для оплати
# =========================
@app.route("/ipn", methods=["POST"])
def ipn():
    secret = request.headers.get("X-IPN-Secret")
    if secret != IPN_SECRET:
        return jsonify({"status": "unauthorized"}), 403

    data = request.json
    user_id = data.get("order_id")
    status = data.get("payment_status")
    currency = data.get("pay_currency")
    amount = data.get("price_amount")

    if status == "finished" and user_id:
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
# Callback для кнопок Inline
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "back":
        services_handler(call.message)
    elif call.data == "pay_usdt":
        create_nowpayments_invoice(call.message)

# =========================
# Функція створення інвойсу NowPayments
# =========================
def create_nowpayments_invoice(message):
    chat_id = message.chat.id
    amount = 1
    currency = "usdttrc20"

    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "price_amount": amount,
        "price_currency": currency,
        "pay_currency": currency,
        "order_id": str(chat_id),
        "order_description": "Оплата юридичних послуг",
        "success_url": f"https://t.me/{bot.get_me().username}",
        "cancel_url": f"https://t.me/{bot.get_me().username}"
    }

    try:
        response = requests.post("https://api.nowpayments.io/v1/payment", json=payload, headers=headers)
        data = response.json()
        payment_url = data.get("invoice_url")

        if payment_url:
            bot.send_message(chat_id, f"💳 Натисніть для оплати 👇\n{payment_url}")
        else:
            bot.send_message(chat_id, "⚠️ Не вдалося створити оплату. Спробуйте пізніше.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Помилка: {e}")

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
