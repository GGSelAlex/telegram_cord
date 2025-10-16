import os
import requests
import telebot
from flask import Flask, request
import shelve
from requests.exceptions import RequestException, HTTPError

# =========================
# Конфігурація та Константи
# =========================
TOKEN = os.getenv("BOT_TOKEN")
# Переконайтеся, що змінні оточення BOT_TOKEN, ADMIN1_ID, ETH_BSC_API_KEY встановлені
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

# Шаблони повідомлень
MESSAGES = {
    "START_WELCOME": (
        "*Kovalova Stanislava: Ваш стратегічний юридичний партнер у складних рішеннях.*\n"
        "Вітаємо в просторі, де закон працює на ваш захист.\n"
        "Наша команда пропонує преміальний рівень юридичного супроводу:\n"
        "🔹 *Конфіденційність*: Повна та безумовна.\n"
        "🔹 *Комплексність*: Від первинної консультації до фінального рішення.\n"
        "🔹 *Результат*: Чітка правова позиція для вашої безпеки."
    ),
    "MAIN_MENU_RETURN": "✅ Ви повернулися до *Головного Меню*. Оберіть розділ 👇",
    "SERVICES_MENU": "Оберіть, будь ласка, вид послуги:",
    "CONSULTATION": "💬 Для *первинної* консультації, будь ласка, надішліть деталі свого запиту. Менеджер відповість Вам найближчим часом.",
    "PREMIUM": (
        "🚀 *PREMIUM ЮРИДИЧНИЙ СУПРОВІД*\n\n"
        "Цей пакет включає 100% гарантію результату та повний захист.\n"
        "• Особистий юрист 24/7.\n"
        "• Супровід на ВЛК (за необхідності).\n"
        "• Екстрена підготовка документів (1 день).\n"
        "• Всі державні мита та збори включені.\n\n"
        "Надішліть запит, щоб отримати індивідуальну пропозицію."
    ),
    "HOTLINE": (
        "📞 *ГАРАНТОВАНА ГАРЯЧА ЛІНІЯ 24/7*\n\n"
        "Отримайте прямий зв'язок з юристом для екстрених ситуацій. Доступно лише для клієнтів, які розпочали співпрацю.\n\n"
        "Для підключення до Гарячої Лінії, оберіть *'Premium Супровід'* або розпочніть роботу з одним із пакетів послуг."
    ),
    "NETWORK_CHOICE": "Оберіть мережу для оплати 1 USDT:",
}

# Flask та Стан користувача (у RAM для простоти, але краще Redis/shelve)
app = Flask(__name__)
user_network_choice = {}  # chat_id -> мережа
HASH_DB_NAME = 'processed_hashes'


# =========================
# Допоміжні функції
# =========================
def notify_admin(text):
    """Надсилає повідомлення всім адміністраторам."""
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            try:
                bot.send_message(admin_id, text)
            except telebot.apihelper.ApiException:
                print(f"Помилка відправки повідомлення адміністратору {admin_id}")

def show_main_menu_inline(chat_id, text=MESSAGES["MAIN_MENU_RETURN"], message_id=None):
    """Генерує та відправляє/редагує головне меню з inline-кнопками."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    btn_services = telebot.types.InlineKeyboardButton("⚖️ Послуги", callback_data="show_services_menu")
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="show_consultation")
    btn_premium = telebot.types.InlineKeyboardButton("🌟 Premium Супровід", callback_data="show_premium")
    btn_hotline = telebot.types.InlineKeyboardButton("📞 Гаряча Лінія 24/7", callback_data="show_hotline")
    
    markup.add(btn_services, btn_consultation, btn_premium, btn_hotline)
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        # На всякий випадок видаляємо стару Reply-клавіатуру
        try:
            bot.send_message(chat_id, ".", reply_markup=telebot.types.ReplyKeyboardRemove())
        except Exception:
            pass

def send_services_category_menu(chat_id, message_id):
    """Редагує повідомлення на меню категорій послуг з INLINE-кнопками."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2) 
    markup.row(
        telebot.types.InlineKeyboardButton("ВИЇЗД", callback_data="service_ВИЇЗД"),
        telebot.types.InlineKeyboardButton("ВІДТЕРМІНУВАННЯ", callback_data="service_ВІДТЕРМІНУВАННЯ")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("ІНВАЛІДНІСТЬ", callback_data="service_ІНВАЛІДНІСТЬ"),
        telebot.types.InlineKeyboardButton("ЗВІЛЬНЕННЯ", callback_data="service_ЗВІЛЬНЕННЯ")
    )
    markup.row(telebot.types.InlineKeyboardButton("🔙 Назад до головного", callback_data="back_to_main_menu"))
    
    bot.edit_message_text(MESSAGES["SERVICES_MENU"], chat_id, message_id, reply_markup=markup)


def send_service_details(chat_id, service_name, message_id):
    """Редагує повідомлення з деталізованою інформацією про послугу з INLINE-кнопками."""
    service = SERVICES[service_name]
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="show_consultation")
    btn_payment = telebot.types.InlineKeyboardButton("Оплата USDT", callback_data="start_usdt_payment")
    btn_back_to_services = telebot.types.InlineKeyboardButton("🔙 До послуг", callback_data="show_services_menu")
    btn_back_to_main = telebot.types.InlineKeyboardButton("🔙 Назад до головного", callback_data="back_to_main_menu")
    
    markup.row(btn_consultation, btn_payment)
    markup.row(btn_back_to_services, btn_back_to_main)
    
    doc_text = "\n".join([f"• {d}" for d in service["docs"]])
    full_text = f"*{service_name}*\n\n{service['text']}\n\n*Документи:*\n{doc_text}"
    
    bot.edit_message_text(full_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)


def send_network_choice_menu(chat_id, message_id):
    """Редагує повідомлення на INLINE-клавіатуру для вибору мережі."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    
    markup.row(
        telebot.types.InlineKeyboardButton("TRC20", callback_data="network_TRC20"),
        telebot.types.InlineKeyboardButton("BSC", callback_data="network_BSC"),
        telebot.types.InlineKeyboardButton("ETH", callback_data="network_ETH")
    )
    markup.row(telebot.types.InlineKeyboardButton("🔙 Назад до головного", callback_data="back_to_main_menu"))

    bot.edit_message_text(MESSAGES["NETWORK_CHOICE"], chat_id, message_id, reply_markup=markup)


# =========================
# Обробники команд та старту
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    # Очищаємо стан користувача при старті
    if chat_id in user_network_choice:
        del user_network_choice[chat_id]
        
    show_main_menu_inline(chat_id, text=MESSAGES["START_WELCOME"])
    notify_admin(f"Новий користувач: {chat_id} ({message.from_user.first_name})")


# =========================
# Обробники Inline-кнопок (Модульні)
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
def handle_back_to_main(call):
    """Повернення до головного меню та очищення стану."""
    chat_id = call.message.chat.id
    
    bot.answer_callback_query(call.id)
    if chat_id in user_network_choice:
        del user_network_choice[chat_id]
        
    show_main_menu_inline(chat_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_") or call.data == "start_usdt_payment")
def handle_main_options(call):
    """Обробка основних опцій: Послуги, Консультація, Premium, Гаряча Лінія, Оплата."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    
    bot.answer_callback_query(call.id)
        
    if data == "show_services_menu":
        send_services_category_menu(chat_id, message_id)
        
    elif data == "show_consultation":
        bot.edit_message_text(MESSAGES["CONSULTATION"], chat_id, message_id, parse_mode="Markdown", reply_markup=None)
        
    elif data == "show_premium":
        bot.edit_message_text(MESSAGES["PREMIUM"], chat_id, message_id, parse_mode="Markdown", reply_markup=None)

    elif data == "show_hotline":
        bot.edit_message_text(MESSAGES["HOTLINE"], chat_id, message_id, parse_mode="Markdown", reply_markup=None)
        
    elif data == "start_usdt_payment":
        send_network_choice_menu(chat_id, message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def handle_service_selection(call):
    """Обробка вибору конкретної послуги."""
    service_name = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    send_service_details(call.message.chat.id, service_name, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("network_"))
def handle_network_selection(call):
    """Обробка вибору мережі для оплати."""
    chat_id = call.message.chat.id
    network = call.data.split("_")[1]
    
    bot.answer_callback_query(call.id)
    user_network_choice[chat_id] = network
    wallet = WALLETS[network]
    
    text = f"💳 Оплата 1 USDT через {network}\nАдреса: `{wallet}`\n\nНадішліть боту TX Hash для перевірки."
    
    # Видаляємо inline-кнопки вибору мережі перед відправкою хешу
    bot.edit_message_text(call.message.text, chat_id, call.message.message_id, reply_markup=None)
    
    bot.send_message(chat_id, text, parse_mode="Markdown")


# =========================
# Перевірка TX Hash (НАДІЙНІСТЬ)
# =========================
@bot.message_handler(func=lambda m: m.text.startswith("0x") or m.text.startswith("T"))
def check_tx_hash(message):
    tx_hash = message.text.strip()
    chat_id = message.chat.id
    network = user_network_choice.get(chat_id)

    if not network:
        bot.send_message(chat_id, "❌ Спочатку оберіть мережу для оплати.")
        return
        
    # 1. Перевірка на повторний хеш у сховищі
    with shelve.open(HASH_DB_NAME) as db:
        if tx_hash in db:
            bot.send_message(chat_id, "⚠️ Ця транзакція вже була успішно оброблена раніше.")
            return

    try:
        # Логіка перевірки TRC20 (Tronscan)
        if network == "TRC20":
            url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Підніме HTTPError
            resp = response.json()
            
            confirmed = resp.get("ret", [{}])[0].get("contractRet") == "SUCCESS"
            
            if confirmed:
                to_address = resp.get("to")
                amount = int(resp.get("contractData", {}).get("amount", 0)) / 1_000_000
                
                if to_address == WALLETS["TRC20"] and amount == 1:
                    with shelve.open(HASH_DB_NAME) as db:
                        db[tx_hash] = chat_id
                        
                    bot.send_message(chat_id, "✅ Оплата 1 USDT TRC20 підтверджена! Менеджер скоро зв'яжеться з Вами.")
                    notify_admin(f"Користувач {chat_id} сплатив 1 USDT TRC20. TX: {tx_hash}")
                    del user_network_choice[chat_id] 
                else:
                    bot.send_message(chat_id, "❌ Транзакція успішна, але дані (адреса/сума) не збігаються.")
            else:
                bot.send_message(chat_id, "❌ Транзакція ще не підтверджена або не вдалася.")
        
        # Логіка перевірки BSC/ETH (BscScan/Etherscan)
        else:
            url = f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}" if network == "BSC" else \
                  f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETH_BSC_API_KEY}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status() 
            resp = response.json()
            
            result = resp.get("result")
            status = result.get("status") if isinstance(result, dict) else result
            
            if status == "1":
                with shelve.open(HASH_DB_NAME) as db:
                    db[tx_hash] = chat_id
                    
                bot.send_message(chat_id, f"✅ Транзакція {tx_hash} підтверджена {network}! Менеджер скоро зв'яжеться з Вами.")
                notify_admin(f"Користувач {chat_id} сплатив 1 USDT {network}. TX: {tx_hash}")
                del user_network_choice[chat_id] 
            else:
                bot.send_message(chat_id, f"❌ Транзакція ще не підтверджена або некоректна {network}. Спробуйте пізніше.")
                
    # 2. Специфічна обробка помилок
    except HTTPError as e:
        error_message = f"❌ Помилка HTTP під час перевірки {network} (Status {e.response.status_code}): {e}"
        bot.send_message(chat_id, "❌ Помилка зв'язку з API-сервісом. Спробуйте пізніше або перевірте TX Hash.")
        notify_admin(error_message)
    except RequestException as e:
        error_message = f"❌ Мережева помилка при перевірці {network}: {e}"
        bot.send_message(chat_id, "❌ Виникла мережева помилка. Спробуйте пізніше.")
        notify_admin(error_message)
    except Exception as e:
        error_message = f"❌ Невідома помилка при обробці TX Hash для {network}: {e}"
        bot.send_message(chat_id, "❌ Виникла невідома помилка обробки. Зверніться до підтримки.")
        notify_admin(error_message)

        
# =========================
# Обробник невідомих повідомлень (UX)
# =========================
@bot.message_handler(func=lambda m: True)
def handle_unknown_messages(message):
    chat_id = message.chat.id
    
    if chat_id in user_network_choice:
        bot.send_message(chat_id, "⚠️ Очікую TX Hash для підтвердження оплати. Якщо ви передумали, скористайтеся командою /start.")
    else:
        show_main_menu_inline(chat_id, text="Я вас не зрозумів. Будь ласка, оберіть дію з меню:")

        
# =========================
# Flask webhook (Інфраструктура)
# =========================
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Bot is running via webhook", 200

# =========================
# Запуск сервера
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
