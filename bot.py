import telebot
import os
import requests
import hmac
import hashlib
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ==== НАЛАШТУВАННЯ ====
BOT_TOKEN = os.getenv("BOT_TOKEN")
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
IPN_SECRET = os.getenv("IPN_SECRET")

ADMIN_IDS = []
if os.getenv("ADMIN1_ID"):
    ADMIN_IDS.append(int(os.getenv("ADMIN1_ID")))
if os.getenv("ADMIN2_ID"):
    ADMIN_IDS.append(int(os.getenv("ADMIN2_ID")))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ==== МЕНЮ ====
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🧳 Виїзд за кордон"), KeyboardButton("🕒 Відтермінування"))
    kb.add(KeyboardButton("♿ Інвалідність"), KeyboardButton("🪖 Звільнення"))
    return kb

def back_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("⬅️ Назад у меню"))
    kb.add(KeyboardButton("💬 Консультація"), KeyboardButton("💳 Оплатити USDT (TRC20)"))
    return kb

# ==== START ====
@bot.message_handler(commands=['start'])
def start(msg):
    user = msg.from_user
    for admin in ADMIN_IDS:
        bot.send_message(admin, f"👤 Новий користувач: @{user.username} (ID: {user.id})")
    welcome = (
        "👋 Вітаємо у *Kovalova Stanislava — Юридичні послуги для чоловіків*\n\n"
        "Ми надаємо:\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ\n\n"
        "Оберіть потрібну послугу 👇"
    )
    bot.send_message(msg.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

# ==== ПОСЛУГИ ====
@bot.message_handler(func=lambda msg: msg.text == "🧳 Виїзд за кордон")
def abroad(msg):
    text = (
        "🌍 *Виїзд за кордон*\n\n"
        "Білий квиток: Ваш Шлях до Свободи та Спокою\n"
        "Ми допоможемо легально виїхати за межі України.\n\n"
        "📄 Ви отримуєте:\n"
        "• Тимчасове посвідчення\n"
        "• ВЛК\n"
        "• Довідка на право виїзду\n\n"
        "⏱️ Термін оформлення: 5–7 днів."
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=back_menu())

@bot.message_handler(func=lambda msg: msg.text == "🕒 Відтермінування")
def deferment(msg):
    text = (
        "📑 *Відтермінування мобілізації*\n\n"
        "Отримайте офіційну відстрочку на рік по стану здоров'я.\n\n"
        "📄 Ви отримуєте:\n"
        "• Тимчасове посвідчення\n"
        "• Довідка (відстрочка на рік)\n"
        "• ВЛК\n\n"
        "⏱️ Термін: 3–5 днів."
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=back_menu())

@bot.message_handler(func=lambda msg: msg.text == "♿ Інвалідність")
def disability(msg):
    text = (
        "♿ *Оформлення інвалідності*\n\n"
        "Комплексна послуга з оформлення групи інвалідності (ІІ або ІІІ).\n\n"
        "📄 Ви отримуєте:\n"
        "• ЛЛК\n"
        "• Довідку ЕКОПФ (МСЕК)\n"
        "• Право на пенсію\n\n"
        "⏱️ Термін: 14–18 днів."
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=back_menu())

@bot.message_handler(func=lambda msg: msg.text == "🪖 Звільнення")
def release(msg):
    text = (
        "🪖 *Звільнення зі служби в ЗСУ*\n\n"
        "Індивідуальний підхід до вашої ситуації.\n\n"
        "📄 Ви отримуєте:\n"
        "• Витяг з наказу\n"
        "• Тимчасове посвідчення\n"
        "• ВЛК\n\n"
        "⏱️ Термін: 7–10 днів."
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=back_menu())

# ==== КОНСУЛЬТАЦІЯ ====
@bot.message_handler(func=lambda msg: msg.text == "💬 Консультація")
def consult(msg):
    bot.send_message(
        msg.chat.id,
        "📞 Для запису на консультацію напишіть юристу напряму:\n👉 @Kovalova_Stanislava"
    )

# ==== ОПЛАТА USDT TRC20 ====
@bot.message_handler(func=lambda msg: msg.text == "💳 Оплатити USDT (TRC20)")
def pay(msg):
    amount_usd = 50
    payload = {
        "price_amount": amount_usd,
        "price_currency": "usd",
        "pay_currency": "usdttrc20",  # USDT TRC20
        "ipn_callback_url": "https://твій-домен.onrender.com/ipn",
        "order_id": str(msg.chat.id),
        "order_description": "Оплата юридичної консультації"
    }
    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    r = requests.post("https://api.nowpayments.io/v1/payment", json=payload, headers=headers)
    data = r.json()
    if "invoice_url" in data:
        text = (
            f"💰 Сума до оплати: {amount_usd} USDT (TRC20)\n"
            f"🔗 Оплатити зараз: {data['invoice_url']}\n\n"
            "Після оплати бот автоматично підтвердить ваш платіж ✅"
        )
        bot.send_message(msg.chat.id, text)
    else:
        bot.send_message(msg.chat.id, f"⚠️ Помилка створення платежу: {data}")

# ==== IPN (NowPayments) ====
@app.route("/ipn", methods=["POST"])
def ipn():
    data = request.json
    received_hmac = request.headers.get("x-nowpayments-sig")
    payload = request.get_data()
    calc_hmac = hmac.new(
        bytes(IPN_SECRET, 'utf-8'),
        msg=payload,
        digestmod=hashlib.sha512
    ).hexdigest()

    if received_hmac != calc_hmac:
        return "Invalid signature", 403

    if data.get("payment_status") == "finished":
        user_id = int(data.get("order_id"))
        bot.send_message(user_id, "✅ Оплату отримано! Юрист зв’яжеться з вами найближчим часом.")
        for admin in ADMIN_IDS:
            bot.send_message(admin, f"💸 Отримано оплату від користувача {user_id}")
    return "OK", 200

# ==== НАЗАД У МЕНЮ ====
@bot.message_handler(func=lambda msg: msg.text == "⬅️ Назад у меню")
def back(msg):
    bot.send_message(msg.chat.id, "🔙 Ви повернулись у головне меню:", reply_markup=main_menu())

# ==== ЗАПУСК ====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
