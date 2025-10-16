import os
import requests
from flask import Flask, request
import telebot

# =========================
# Конфігурація
# =========================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [
    int(os.getenv("ADMIN1_ID", 0)),
    int(os.getenv("ADMIN2_ID", 0))
]

# Гаманці
WALLETS = {
    "TRC20": "TT2BVxXgZuMbspJM2DTuntnTetnY5e8ntF",
    "BSC": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5",
    "ETH": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5"
}

ETH_BSC_API_KEY = os.getenv("ETH_BSC_API_KEY")

# Послуги
SERVICES = {
    "ВИЇЗД": {
        "text": "Білий квиток: Ваш Шлях до Свободи та Спокою\nПовна легальна підтримка для виїзду за кордон.",
        "docs": ["Тимчасове посвідчення", "ВЛК", "Довідка на право на виїзд"]
    },
    "ІНВАЛІДНІСТЬ": {
        "text": "Група Інвалідності: Ваше Право на Захист та Соціальні Гарантії",
        "docs": ["ВЛК", "Довідка ЕКОПФ (МСЕК)", "Право на пенсію"]
    },
    "ВІДТЕРМІНУВАННЯ": {
        "text": "Отстрочка на год робимо протягом 3-5 днів по стану здоров'я (ВЛК). Можна пересуватися по Україні.",
        "docs": ["Тимчасове посвідчення", "Довідка (відтермінування на рік)", "ВЛК"]
    },
    "ЗВІЛЬНЕННЯ": {
        "text": "Індивідуальний підхід та повний юридичний супровід для звільнення з ЗСУ.",
        "docs": ["Пакет документів для звільнення", "ВЛК", "Рапорти та клопотання"]
    }
}

# Flask
app = Flask(__name__)

# =========================
# Функції
# =========================
def notify_admin(text):
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, text)

def send_service_details(chat_id, service_name):
    service = SERVICES[service_name]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💬 Консультація", url="https://t.me/uristcord")
    )
    markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    doc_text = "\n".join([f"• {d}" for d in service["docs"]])
    full_text = f"*{service_name}*\n\n{service['text']}\n\n*Документи:*\n{doc_text}"
    bot.send_message(chat_id, full_text, parse_mode="Markdown", reply_markup=markup)

# =========================
# Головне меню
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "Оплата USDT")
    markup.row("💬 Консультація")
    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)
    notify_admin(f"Новий користувач натиснув /start: {chat_id} ({message.from_user.first_name})")

# =========================
# Послуги
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
    wallet = WALLETS[network]
    amount = 1
    text = (
        f"💳 Оплата {amount} USDT через {network}\n\n"
        f"Адреса для переказу:\n`{wallet}`\n\n"
        "Після переказу надішліть боту TX Hash транзакції для перевірки."
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

# =========================
# Перевірка TX Hash
# =========================
@bot.message_handler(func=lambda m: m.text.startswith("0x") or m.text.startswith("T"))
def check_tx_hash(message):
    tx_hash = message.text.strip()
    chat_id = message.chat.id

    # TRC20
    if tx_hash.startswith("T"):
        url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
        try:
            resp = requests.get(url).json()
            to_address = resp.get("to")
            amount = int(resp.get("contractData", {}).get("amount", 0)) / 1_000_000
            confirmed = resp.get("ret", [{}])[0].get("contractRet") == "SUCCESS"
            if confirmed and to_address == WALLETS["TRC20"] and amount == 1:
                bot.send_message(chat_id, f"✅ Оплата {amount} USDT TRC20 підтверджена!")
                notify_admin(f"Користувач {chat_id} сплатив {amount} USDT TRC20. TX: {tx_hash}")
            else:
                bot.send_message(chat_id, f"❌ Транзакція не підтверджена або дані не збігаються")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Помилка TRC20: {e}")

    # BSC / ETH
    elif tx_hash.startswith("0x"):
        # Визначаємо мережу за замовчуванням BSC
        chain_id = 56
        network_name = "BSC"
        url = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}"
        try:
            resp = requests.get(url).json()
            tx = resp.get("result")
            if not isinstance(tx, dict):
                bot.send_message(chat_id, "❌ Транзакція не знайдена або формат відповіді некоректний")
                return
            to_address = tx.get("to", "").lower()
            value = int(tx.get("value", "0"), 16) / 1e6
            if to_address == WALLETS[network_name].lower() and value == 1:
                bot.send_message(chat_id, f"✅ Оплата {value} USDT {network_name} підтверджена!")
                notify_admin(f"Користувач {chat_id} сплатив {value} USDT {network_name}. TX: {tx_hash}")
            else:
                bot.send_message(chat_id, f"❌ Транзакція не підтверджена або дані не збігаються")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Помилка {network_name}: {e}")

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
    bot.set_webhook(url=f"https://{os
