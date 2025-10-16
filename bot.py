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
    """Надсилає повідомлення всім адміністраторам."""
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, text)

def send_service_details(chat_id, service_name):
    """Відправляє деталізовану інформацію про послугу з INLINE-кнопками."""
    service = SERVICES[service_name]
    
    # Створюємо INLINE-клавіатуру
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопки послуги - всі INLINE
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="consultation")
    btn_payment = telebot.types.InlineKeyboardButton("Оплата USDT", callback_data="start_usdt_payment")
    btn_back_main = telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")
    
    markup.row(btn_consultation, btn_payment)
    markup.row(btn_back_main)
    
    doc_text = "\n".join([f"• {d}" for d in service["docs"]])
    full_text = f"*{service_name}*\n\n{service['text']}\n\n*Документи:*\n{doc_text}"
    
    # Надсилаємо повідомлення з INLINE-кнопками
    bot.send_message(chat_id, full_text, parse_mode="Markdown", reply_markup=markup)

def show_main_menu_inline(chat_id):
    """Генерує та відправляє головне меню з inline-кнопками."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # Головні INLINE-кнопки
    btn_services = telebot.types.InlineKeyboardButton("⚖️ Послуги", callback_data="show_services")
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="consultation")
    btn_premium = telebot.types.InlineKeyboardButton("🌟 Premium Супровід", callback_data="show_premium")
    btn_hotline = telebot.types.InlineKeyboardButton("📞 Гаряча Лінія 24/7", callback_data="show_hotline")
    
    markup.add(btn_services, btn_consultation, btn_premium, btn_hotline)
    
    bot.send_message(chat_id, "✅ Ви повернулися до *Головного Меню*:", 
                     parse_mode="Markdown", reply_markup=markup)

# =========================
# Меню та Привітання
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    # 1. Створення InlineKeyboardMarkup
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # Створення Inline-кнопок з callback_data
    btn_services = telebot.types.InlineKeyboardButton("⚖️ Послуги", callback_data="show_services")
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="consultation")
    btn_premium = telebot.types.InlineKeyboardButton("🌟 Premium Супровід", callback_data="show_premium")
    btn_hotline = telebot.types.InlineKeyboardButton("📞 Гаряча Лінія 24/7", callback_data="show_hotline")

    markup.add(btn_services, btn_consultation, btn_premium, btn_hotline)
    
    # ТЕКСТ ПРИВІТАННЯ
    welcome_text = (
        "*Kovalova Stanislava: Ваш стратегічний юридичний партнер у складних рішеннях.*\n"
        "Вітаємо в просторі, де закон працює на ваш захист.\n"
        "Ми розуміємо, що правові питання, пов'язані з військовим обліком, виїздом за кордон, "
        "отриманням відтермінування або процедурою звільнення з ЗСУ через інвалідність чи "
        "сімейні обставини, вимагають не лише знання, а й бездоганного досвіду.\n\n"
        "Наша команда пропонує преміальний рівень юридичного супроводу:\n"
        "🔹 *Конфіденційність*: Повна та безумовна.\n"
        "🔹 *Комплексність*: Від первинної консультації до фінального рішення.\n"
        "🔹 *Результат*: Чітка правова позиція для вашої безпеки."
    )
    
    # Надсилання повідомлення з Inline-кнопками
    bot.send_message(
        chat_id, 
        welcome_text,
        parse_mode="Markdown", 
        reply_markup=markup
    )
    
    # Видаляємо можливу стару Reply-клавіатуру
    bot.send_message(chat_id, "Оберіть розділ:", reply_markup=telebot.types.ReplyKeyboardRemove())
    
    notify_admin(f"Новий користувач: {chat_id} ({message.from_user.first_name})")

# =========================
# Меню Послуг (ReplyKeyboardMarkup)
# =========================
@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services_handler(message):
    chat_id = message.chat.id
    # Створюємо стандартну Reply-клавіатуру для вибору категорії послуг
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True) 
    markup.row("ВИЇЗД", "ВІДТЕРМІНУВАННЯ")
    markup.row("ІНВАЛІДНІСТЬ", "ЗВІЛЬНЕННЯ")
    markup.row("🔙 Назад до головного") # Змінено назву, щоб відрізняти від inline-назад
    # Оскільки тут є ReplyKeyboardMarkup, ми не видаляємо її.
    bot.send_message(chat_id, "Ми надаємо:", reply_markup=markup)

# Обробник вибору конкретної послуги з Reply-клавіатури
@bot.message_handler(func=lambda m: m.text in SERVICES.keys())
def service_handler(message):
    # Приховуємо Reply-клавіатуру
    bot.send_message(message.chat.id, "Обрана послуга:", reply_markup=telebot.types.ReplyKeyboardRemove())
    # Надсилаємо деталі з inline-кнопками
    send_service_details(message.chat.id, message.text)

# =========================
# Назад (Текстовий обробник - тільки для повернення з вибору мережі)
# =========================
@bot.message_handler(func=lambda m: m.text == "🔙 Назад до головного")
def go_back_to_main_from_services(message):
    chat_id = message.chat.id
    # Прибираємо Reply-клавіатуру послуг
    bot.send_message(chat_id, "Повернення...", reply_markup=telebot.types.ReplyKeyboardRemove())
    # Переміщення на Головний екран (функція з inline-кнопками)
    show_main_menu_inline(chat_id)

# =========================
# Оплата USDT (ReplyKeyboardMarkup для вибору мережі)
# =========================
@bot.message_handler(func=lambda m: m.text == "Оплата USDT")
@bot.callback_query_handler(func=lambda call: call.data == "start_usdt_payment")
def choose_network(update):
    """Показує ReplyKeyboardMarkup для вибору мережі."""
    if isinstance(update, telebot.types.CallbackQuery):
        chat_id = update.message.chat.id
        bot.answer_callback_query(update.id)
        bot.edit_message_reply_markup(chat_id, update.message.message_id, reply_markup=None) # Прибираємо inline
    else:
        chat_id = update.chat.id
        # Прибираємо Reply-клавіатуру, якщо викликано з текстової кнопки (стара логіка)
        bot.send_message(chat_id, "Обрано оплату:", reply_markup=telebot.types.ReplyKeyboardRemove())

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("TRC20", "BSC", "ETH")
    markup.row("🔙 Назад") # Текстова кнопка, обробляється окремо

    bot.send_message(chat_id, "Оберіть мережу для оплати 1 USDT:", reply_markup=markup)

# Текстовий обробник "Назад" для виходу з вибору мережі
@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def go_back_from_network_choice(message):
    chat_id = message.chat.id
    
    if chat_id in user_network_choice:
        del user_network_choice[chat_id]
        
    # Прибираємо Reply-клавіатуру
    bot.send_message(chat_id, "Повернення...", reply_markup=telebot.types.ReplyKeyboardRemove())
    
    # Переміщення на Головний екран
    show_main_menu_inline(chat_id)


@bot.message_handler(func=lambda m: m.text in ["TRC20", "BSC", "ETH"])
def send_wallet_info(message):
    chat_id = message.chat.id
    network = message.text
    user_network_choice[chat_id] = network
    wallet = WALLETS[network]
    text = f"💳 Оплата 1 USDT через {network}\nАдреса: `{wallet}`\n\nНадішліть боту TX Hash для перевірки."
    bot.send_message(chat_id, text, parse_mode="Markdown")

# =========================
# Обробник Inline-кнопок
# =========================
@bot.callback_query_handler(func=lambda call: call.data in ["show_services", "consultation", "show_premium", "show_hotline", 
                                                            "back_to_main_menu"])
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    bot.answer_callback_query(call.id) 
    
    # Прибираємо inline-кнопки з повідомлення після натискання
    try:
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None) 
    except Exception:
        pass
        
    if call.data == "show_services":
        # Відображаємо меню послуг (з ReplyKeyboardMarkup)
        services_handler(call.message) 
        
    elif call.data == "consultation":
        bot.send_message(chat_id, "💬 Для *первинної* консультації, будь ласка, надішліть деталі свого запиту. Менеджер відповість Вам найближчим часом.", parse_mode="Markdown")

    elif call.data == "show_premium":
        premium_text = (
            "🚀 *PREMIUM ЮРИДИЧНИЙ СУПРОВІД*\n\n"
            "Цей пакет включає 100% гарантію результату та повний захист.\n"
            "• Особистий юрист 24/7.\n"
            "• Супровід на ВЛК (за необхідності).\n"
            "• Екстрена підготовка документів (1 день).\n"
            "• Всі державні мита та збори включені.\n\n"
            "Надішліть запит, щоб отримати індивідуальну пропозицію."
        )
        bot.send_message(chat_id, premium_text, parse_mode="Markdown")

    elif call.data == "show_hotline":
        hotline_text = (
            "📞 *ГАРАНТОВАНА ГАРЯЧА ЛІНІЯ 24/7*\n\n"
            "Отримайте прямий зв'язок з юристом для екстрених ситуацій. Доступно лише для клієнтів, які розпочали співпрацю.\n\n"
            "Для підключення до Гарячої Лінії, оберіть *'Premium Супровід'* або розпочніть роботу з одним із пакетів послуг."
        )
        bot.send_message(chat_id, hotline_text, parse_mode="Markdown")
        
    elif call.data == "back_to_main_menu":
        # Це повертає користувача на головний екран з усіма inline-кнопками
        bot.send_message(chat_id, "Повернення...", reply_markup=telebot.types.ReplyKeyboardRemove())
        show_main_menu_inline(chat_id)

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
                del user_network_choice[chat_id] # Очистка вибору після успіху
            else:
                bot.send_message(chat_id, "❌ Транзакція не підтверджена або дані не збігаються")
        else:
            url = f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}" if network == "BSC" else \
                  f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}"
            resp = requests.get(url).json()
            result = resp.get("result")
            status = result.get("status") if isinstance(result, dict) else result
            if status == "1":
                bot.send_message(chat_id, f"✅ Транзакція {tx_hash} підтверджена {network}!")
                notify_admin(f"Користувач {chat_id} сплатив 1 USDT {network}. TX: {tx_hash}")
                del user_network_choice[chat_id] # Очистка вибору після успіху
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
    # Цей код має працювати лише при першому деплої
    # bot.remove_webhook()
    # bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    return "Bot is running via webhook", 200

# =========================
# Запуск сервера
# =========================
if __name__ == "__main__":
    # Для локального тестування можна використовувати bot.polling(),
    # але для деплою на сервери, як Render, потрібен Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
