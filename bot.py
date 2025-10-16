import os
import requests
from flask import Flask, request
import telebot

# =========================
# Конфігурація
# =========================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
ADMIN_IDS = [int(os.getenv("ADMIN1_ID", 0)), int(os.getenv("ADMIN2_ID", 0))]

# Гаманці
WALLETS = {
    "TRC20": "TT2BVxXgZuMbspJM2DTuntnTetnY5e8ntF",
    "BSC": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5",
    "ETH": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5"
}
ETH_BSC_API_KEY = os.getenv("ETH_BSC_API_KEY")

# Послуги
SERVICES = {
    "ВИЇЗД": {"text": "Білий квиток: Ваш Шлях до Свободи та Спокою\nПовна легальна підтримка для виїзду за кордон.",
               "docs": ["Тимчасове посвідчення", "ВЛК", "Довідка на право на виїзд"]},
    "ІНВАЛІДНІСТЬ": {"text": "Група Інвалідності: Ваше Право на Захист та Соціальні Гарантії",
                     "docs": ["ВЛК", "Довідка ЕКОПФ (МСЕК)", "Право на пенсію"]},
    "ВІДТЕРМІНУВАННЯ": {"text": "Отстрочка на год робимо протягом 3-5 днів по стану здоров'я (ВЛК). Можна пересуватися по Україні.",
                        "docs": ["Тимчасове посвідчення", "Довідка (відтермінування на рік)", "ВЛК"]},
    "ЗВІЛЬНЕННЯ": {"text": "Індивідуальний підхід та повний юридичний супровід для звільнення з ЗСУ.",
                    "docs": ["Пакет документів для звільнення", "ВЛК", "Рапорти та клопотання"]}
}

# Flask
app = Flask(__name__)
user_network_choice = {}  # chat_id -> мережа

# =========================
# Функції
# =========================
def notify_admin(text):
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, text)

def send_service_details(chat_id, service_name):
    service = SERVICES[service_name]
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💬 Консультація", "Оплата USDT")
    markup.row("🔙 Назад")
    doc_text = "\n".join([f"• {d}" for d in service["docs"]])
    full_text = f"*{service_name}*\n\n{service['text']}\n\n*Документи:*\n{doc_text}"
    bot.send_message(chat_id, full_text, parse_mode="Markdown", reply_markup=markup)

# =========================
# Меню
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги")
    markup.row("💬 Консультація")
    bot.send_message(chat_id, "💼 *Юридичні послуги Kovalova Stanislava*\nВітаємо! Оберіть розділ 👇",
                     parse_mode="Markdown", reply_markup=markup)
    notify_admin(f"Новий користувач: {chat_id} ({message.from_user.first_name})")

@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services_handler(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("ВИЇЗД", "ВІДТЕРМІНУВАННЯ")
    markup.row("ІНВАЛІДНІСТЬ", "ЗВІЛЬНЕННЯ")
    markup.row("🔙 Назад")
    bot.send_message(chat_id, "Ми надаємо:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in SERVICES.keys())
def service_handler(message):
    send_service_details(message.chat.id, message.text)

# =========================
# Назад
# =========================
@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def go_back(message):
    chat_id = message.chat.id
    if chat_id in user_network_choice:
        choose_network(message)
    else:
        services_handler(message)

# =========================
# Оплата USDT
# =========================
@bot.message_handler(func=lambda m: m.text == "Оплата USDT")
def choose_network(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("TRC20", "BSC", "ETH")
    markup.row("🔙 Назад")
    bot.send_message(chat_id, "Оберіть мережу для оплати 1 USDT:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["TRC20", "BSC", "ETH"])
def send_wallet_info(message):
    chat_id = message.chat.id
    network = message.text
    user_network_choice[chat_id] = network
    wallet = WALLETS[network]
    text = f"💳 Оплата 1 USDT через {network}\nАдреса: `{wallet}`\n\nНадішліть боту TX Hash для перевірки."
    bot.send_message(chat_id, text, parse_mode="Markdown")

# =========================
# Перевірка TX Hash
# =========================
@bot.message_handler(func=lambda m: m.text.startswith("0x") or m.text.startswith("T"))
def check_tx_hash(message):
    tx_hash = message.text.strip()
    chat_id = message.chat.id
    network = user_network_choice.get(chat_id)
    if not network:
        bot.send_message(chat_id, "❌ Спочатку оберіть мережу для оплати.")
        return
    try:
        if network == "TRC20":
            url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
            resp = requests.get(url).json()
            to_address = resp.get("to")
            amount = int(resp.get("contractData", {}).get("amount", 0)) / 1_000_000
            confirmed = resp.get("ret", [{}])[0].get("contractRet") == "SUCCESS"
            if confirmed and to_address == WALLETS["TRC20"] and amount == 1:
                bot.send_message(chat_id, "✅ Оплата 1 USDT TRC20 підтверджена!")
                notify_admin(f"Користувач {chat_id} сплатив 1 USDT TRC20. TX: {tx_hash}")
            else:
                bot.send_message(chat_id, "❌ Транзакція не підтверджена або дані не збігаються")
        else:
            url = f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}" if network == "BSC" else \
                  f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}"
            resp = requests.get(url).json()
            result = resp.get("result")
            status = result.get("status") if isinstance(result, dict) else result  # рядок або словник
            if status == "1":
                bot.send_message(chat_id, f"✅ Транзакція {tx_hash} підтверджена {network}!")
                notify_admin(f"Користувач {chat_id} сплатив 1 USDT {network}. TX: {tx_hash}")
            else:
                bot.send_message(chat_id, f"❌ Транзакція ще не підтверджена або некоректна {network}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Помилка {network}: {e}")

# =========================
# Flask webhook
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
# Запуск сервера
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
