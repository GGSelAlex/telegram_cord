import os
import requests
import telebot
from flask import Flask, request
import shelve
import sys 
from requests.exceptions import RequestException, HTTPError

# =========================
# Конфігурація та Константи
# =========================
TOKEN = os.getenv("BOT_TOKEN")
# Переконайтеся, що змінні оточення BOT_TOKEN, ADMIN1_ID, ETH_BSC_API_KEY встановлені
bot = telebot.TeleBot(TOKEN) 
ADMIN_IDS = [int(os.getenv("ADMIN1_ID", 0)), int(os.getenv("ADMIN2_ID", 0))]
TELEGRAM_LAWYER_USERNAME = os.getenv("LAWYER_USERNAME", "your_lawyer_username") # <-- ЗМІНІТЬ НА РЕАЛЬНИЙ USERNAME ЮРИСТА

# Гаманці
WALLETS = {
    "TRC20": "TT2BVxXgZuMbspJM2DTuntnTetnY5e8ntF",
    "BSC": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5",
    "ETH": "0xc8872cac097911Bfa3203d5c9225c4CdE2A882B5"
}
ETH_BSC_API_KEY = os.getenv("ETH_BSC_API_KEY")

# Назви DB для shelve (для стійкого зберігання)
HASH_DB_NAME = 'processed_hashes'
USER_STATE_DB_NAME = 'user_states' 

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
    "CONSULTATION_MENU": (
        "💬 *Первинна Консультація*\n\n"
        "Оберіть, як Вам зручніше надіслати запит:"
    ),
    "PREMIUM": (
        "🚀 *PREMIUM ЮРИДИЧНИЙ СУПРОВІД*\n\n"
        "Цей пакет включає 100% гарантію результату та повний захист.\n"
        "• Особистий юрист 24/7.\n"
        "• Супровід на ВЛК (за необхідності).\n"
        "• Екстрена підготовка документів (1 день).\n"
        "• Всі державні мита та збори включені.\n\n"
        "Надішліть запит, щоб отримати індивідуальну пропозицію."
    ),
    "NETWORK_CHOICE": "Оберіть мережу для оплати 1 USDT:",
    
    # НОВІ ШАБЛОНИ ДЛЯ АДМІН-СПОВІЩЕНЬ
    "ADMIN_NEW_USER": "Новий користувач: {user_link} (ID: `{chat_id}`)",
    "ADMIN_PAID_SUCCESS": "Користувач {user_link} сплатив 1 USDT {network}. TX: `{tx_hash}`",
    "ADMIN_PAID_INVALID": "⚠️ НЕПРАВИЛЬНА СУМА/АДРЕСА ({network}) від {user_link}. TX: `{tx_hash}`",
    "ADMIN_PAID_UNCONFIRMED": "⚠️ НЕПІДТВЕРДЖЕНА {network} від {user_link}. TX: `{tx_hash}`",
    "ADMIN_NEW_CONSULT_TEXT": "🔥 НОВИЙ ЗАПИТ НА КОНСУЛЬТАЦІЮ від {user_link} (ID: `{chat_id}`):\n\n{query}",
    "ADMIN_NEW_CONSULT_VOICE": "🔥 НОВИЙ ГОЛОСОВИЙ ЗАПИТ НА КОНСУЛЬТАЦІЮ від {user_link} (ID: `{chat_id}`)",
}

# Flask
app = Flask(__name__)


# =========================
# Допоміжні функції
# =========================
def notify_admin(text):
    """Надсилає повідомлення всім адміністраторам (в Markdown)."""
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            try:
                bot.send_message(admin_id, text, parse_mode="Markdown")
            except telebot.apihelper.ApiException:
                print(f"Помилка відправки повідомлення адміністратору {admin_id}")

def get_user_link(message):
    """Створює Markdown-посилання для адміністратора."""
    chat_id = message.chat.id
    first_name = message.from_user.first_name or f"Користувач {chat_id}"
    return f"[{first_name}](tg://user?id={chat_id})"

def show_main_menu_inline(chat_id, text=MESSAGES["MAIN_MENU_RETURN"], message_id=None):
    """Генерує та відправляє/редагує головне меню з inline-кнопками."""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    btn_services = telebot.types.InlineKeyboardButton("⚖️ Послуги", callback_data="show_services_menu")
    btn_consultation = telebot.types.InlineKeyboardButton("💬 Консультація", callback_data="show_consultation")
    btn_premium = telebot.types.InlineKeyboardButton("🌟 Premium Супровід", callback_data="show_premium")

    markup.add(btn_services, btn_consultation, btn_premium)
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        # Відправка основного меню
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        
        # ВИКОРИСТАННЯ НЕВИДИМОГО СИМВОЛА '\u200b' ЗАМІСТЬ КРАПКИ
        try:
            bot.send_message(chat_id, "\u200b", reply_markup=telebot.types.ReplyKeyboardRemove())
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
    user_link = get_user_link(message)
    
    with shelve.open(USER_STATE_DB_NAME) as db:
        if str(chat_id) in db:
            del db[str(chat_id)]
        
    show_main_menu_inline(chat_id, text=MESSAGES["START_WELCOME"])
    notify_admin(MESSAGES["ADMIN_NEW_USER"].format(user_link=user_link, chat_id=chat_id))


# =========================
# Обробники Inline-кнопок (Модульні)
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
def handle_back_to_main(call):
    """Повернення до головного меню та очищення стану."""
    chat_id = call.message.chat.id
    
    bot.answer_callback_query(call.id)
    with shelve.open(USER_STATE_DB_NAME) as db:
        if str(chat_id) in db:
            del db[str(chat_id)]
        
    show_main_menu_inline(chat_id, message_id=call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_") or call.data == "start_usdt_payment" or call.data == "consultation_direct_to_bot")
def handle_main_options(call):
    """Обробка основних опцій: Послуги, Консультація, Premium, Оплата."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    
    bot.answer_callback_query(call.id)
        
    if data == "show_services_menu":
        send_services_category_menu(chat_id, message_id)
        
    elif data == "show_consultation":
        # Меню консультації
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        btn_direct = telebot.types.InlineKeyboardButton(
            "Написати Юристу Напряму 📝", 
            url=f"https://t.me/{TELEGRAM_LAWYER_USERNAME}"
        )
        btn_bot = telebot.types.InlineKeyboardButton(
            "Надіслати Запит Боту (Текст/Голос) 📥", 
            callback_data="consultation_direct_to_bot"
        )
        markup.add(btn_direct, btn_bot)
        
        bot.edit_message_text(
            MESSAGES["CONSULTATION_MENU"], 
            chat_id, 
            message_id, 
            parse_mode="Markdown", 
            reply_markup=markup
        )
        
    elif data == "consultation_direct_to_bot":
        # Встановлюємо стан, що користувач очікує консультації
        with shelve.open(USER_STATE_DB_NAME) as db:
            db[str(chat_id)] = "AWAITING_CONSULTATION" 
        
        bot.edit_message_text(
            "*✅ Готово!*\n\nБудь ласка, детально опишіть Ваше питання тут. Як тільки Ви надішлете повідомлення, менеджер отримає сповіщення.\n\n_Зверніть увагу: ми очікуємо саме Ваш запит, а не 'Привіт'._",
            chat_id, 
            message_id, 
            parse_mode="Markdown", 
            reply_markup=None
        )
        
    elif data == "show_premium":
        # БЛОК ДЛЯ PREMIUM
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)

        btn_direct = telebot.types.InlineKeyboardButton(
            "Написати Юристу Напряму 📝", 
            url=f"https://t.me/{TELEGRAM_LAWYER_USERNAME}"
        )
        btn_back = telebot.types.InlineKeyboardButton(
            "🔙 Назад до головного", 
            callback_data="back_to_main_menu"
        )

        markup.add(btn_direct, btn_back)
        
        bot.edit_message_text(
            MESSAGES["PREMIUM"], 
            chat_id, 
            message_id, 
            parse_mode="Markdown", 
            reply_markup=markup 
        )
        
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
    
    # Зберігання вибраної мережі в стійкому сховищі
    with shelve.open(USER_STATE_DB_NAME) as db:
        db[str(chat_id)] = network
        
    wallet = WALLETS[network]
    
    text = f"💳 Оплата 1 USDT через {network}\nАдреса: `{wallet}`\n\nНадішліть боту TX Hash для перевірки."
    
    bot.edit_message_text(call.message.text, chat_id, call.message.message_id, reply_markup=None)
    
    bot.send_message(chat_id, text, parse_mode="Markdown")


# =========================
# Перевірка TX Hash (НАДІЙНІСТЬ)
# =========================
@bot.message_handler(func=lambda m: m.text.startswith("0x") or m.text.startswith("T"))
def check_tx_hash(message):
    tx_hash = message.text.strip()
    chat_id = message.chat.id
    user_link = get_user_link(message)
    
    # Отримання стану з DB
    with shelve.open(USER_STATE_DB_NAME) as db:
        network = db.get(str(chat_id))

    if not network or network not in WALLETS:
        bot.send_message(chat_id, "❌ Спочатку оберіть мережу для оплати.")
        return
    
    # Перевірка на вже оброблену транзакцію
    with shelve.open(HASH_DB_NAME) as db:
        if tx_hash in db:
            bot.send_message(chat_id, "⚠️ Ця транзакція вже була успішно оброблена раніше.")
            return

    # Загальне позитивне повідомлення для клієнта
    positive_client_msg = "✅ Чудово! Ми отримали Ваш хеш-код. Очікуйте на підтвердження транзакції. Менеджер зв'яжеться з Вами протягом кількох хвилин."
    
    try:
        # Логіка перевірки TRC20 (Tronscan)
        if network == "TRC20":
            url = f"https://apilist.tronscan.org/api/transaction-info?hash={tx_hash}"
            response = requests.get(url, timeout=10)
            response.raise_for_status() 
            resp = response.json()
            
            confirmed = resp.get("ret", [{}])[0].get("contractRet") == "SUCCESS"
            
            if confirmed:
                to_address = resp.get("to")
                amount = int(resp.get("contractData", {}).get("amount", 0)) / 1_000_000
                
                if to_address == WALLETS["TRC20"] and amount == 1:
                    with shelve.open(HASH_DB_NAME) as db:
                        db[tx_hash] = chat_id
                    with shelve.open(USER_STATE_DB_NAME) as db:
                        if str(chat_id) in db:
                            del db[str(chat_id)]
                        
                    bot.send_message(chat_id, "✅ Оплата 1 USDT TRC20 підтверджена! Менеджер скоро зв'яжеться з Вами.")
                    notify_admin(MESSAGES["ADMIN_PAID_SUCCESS"].format(user_link=user_link, network="TRC20", tx_hash=tx_hash))
                    
                    # Повернення до головного меню після успішної дії
                    show_main_menu_inline(chat_id) 
                else:
                    # Транзакція успішна, але дані не збігаються (потрібна ручна перевірка)
                    bot.send_message(chat_id, positive_client_msg)
                    notify_admin(MESSAGES["ADMIN_PAID_INVALID"].format(user_link=user_link, network="TRC20", tx_hash=tx_hash))
            else:
                # Транзакція ще не підтверджена (потрібна ручна перевірка)
                bot.send_message(chat_id, positive_client_msg)
                notify_admin(MESSAGES["ADMIN_PAID_UNCONFIRMED"].format(user_link=user_link, network="TRC20", tx_hash=tx_hash))
        
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
                with shelve.open(USER_STATE_DB_NAME) as db:
                    if str(chat_id) in db:
                        del db[str(chat_id)]
                        
                bot.send_message(chat_id, f"✅ Транзакція {tx_hash} підтверджена {network}! Менеджер скоро зв'яжеться з Вами.")
                notify_admin(MESSAGES["ADMIN_PAID_SUCCESS"].format(user_link=user_link, network=network, tx_hash=tx_hash))
                
                # Повернення до головного меню після успішної дії
                show_main_menu_inline(chat_id)
            else:
                # Транзакція не підтверджена або некоректна (потрібна ручна перевірка)
                bot.send_message(chat_id, positive_client_msg)
                notify_admin(MESSAGES["ADMIN_PAID_UNCONFIRMED"].format(user_link=user_link, network=network, tx_hash=tx_hash))
                
    except HTTPError as e:
        error_message = f"❌ Помилка HTTP під час перевірки {network} (Status {e.response.status_code}): {e}"
        bot.send_message(chat_id, "❌ Помилка зв'язку з API-сервісом. Спробуйте пізніше або перевірте TX Hash.")
        notify_admin(f"❌ Критична помилка API {network} від {user_link}. HTTP Error: {e.response.status_code}")
    except RequestException as e:
        error_message = f"❌ Мережева помилка при перевірці {network}: {e}"
        bot.send_message(chat_id, "❌ Виникла мережева помилка. Спробуйте пізніше.")
        notify_admin(f"❌ Критична помилка мережі {network} від {user_link}. Error: {e}")
    except Exception as e:
        error_message = f"❌ Невідома помилка при обробці TX Hash для {network}: {e}"
        bot.send_message(chat_id, "❌ Виникла невідома помилка обробки. Зверніться до підтримки.")
        notify_admin(f"❌ Невідома помилка {network} від {user_link}. Error: {e}")

        
# =========================
# Обробник консультаційних запитів
# =========================
@bot.message_handler(func=lambda m: True, content_types=['text', 'voice', 'photo', 'document'])
def handle_consultation_request(message):
    chat_id = message.chat.id
    user_link = get_user_link(message)
    
    with shelve.open(USER_STATE_DB_NAME) as db:
        current_state = db.get(str(chat_id))

    if current_state != "AWAITING_CONSULTATION":
        # Якщо стан не очікує консультації, передаємо в обробник невідомих
        handle_unknown_messages(message)
        return

    # Логіка обробки та сповіщення
    if message.content_type == 'text':
        query = message.text
        notify_admin(MESSAGES["ADMIN_NEW_CONSULT_TEXT"].format(user_link=user_link, chat_id=chat_id, query=query))
        
    elif message.content_type == 'voice':
        notify_admin(MESSAGES["ADMIN_NEW_CONSULT_VOICE"].format(user_link=user_link, chat_id=chat_id))
        # НОВЕ: Пересилаємо голосове повідомлення ВСІМ адміністраторам
        for admin_id in ADMIN_IDS:
            if admin_id != 0:
                try:
                    bot.forward_message(admin_id, chat_id, message.message_id)
                except telebot.apihelper.ApiException:
                    pass
    
    else: # Обробка фото/документів/іншого медіа
        notify_admin(f"🔥 НОВИЙ ЗАПИТ НА КОНСУЛЬТАЦІЮ (ДОКУМЕНТ/ФОТО) від {user_link} (ID: `{chat_id}`)")
        # НОВЕ: Пересилаємо медіафайл ВСІМ адміністраторам
        for admin_id in ADMIN_IDS:
            if admin_id != 0:
                try:
                    bot.forward_message(admin_id, chat_id, message.message_id) 
                except telebot.apihelper.ApiException:
                    pass

    # Фінальне повідомлення клієнту та повернення в меню
    bot.send_message(chat_id, "Дякуємо! Ваш запит отримано та передано менеджеру. Очікуйте відповіді найближчим часом.")
    
    # Очищення стану після отримання запиту
    with shelve.open(USER_STATE_DB_NAME) as db:
        if str(chat_id) in db:
            del db[str(chat_id)]
            
    # Повернення до головного меню
    show_main_menu_inline(chat_id)


# =========================
# Обробник невідомих повідомлень (UX)
# =========================
@bot.message_handler(func=lambda m: True)
def handle_unknown_messages(message):
    chat_id = message.chat.id
    
    with shelve.open(USER_STATE_DB_NAME) as db:
        current_state = db.get(str(chat_id))
    
    if current_state in ["TRC20", "BSC", "ETH"]:
        bot.send_message(chat_id, "⚠️ Очікую TX Hash для підтвердження оплати. Якщо ви передумали, скористайтеся командою /start.")
    elif current_state == "AWAITING_CONSULTATION":
        # Це вже обробляється в handle_consultation_request, але тут на всяк випадок
        pass 
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
# Запуск сервера (з перевіркою)
# =========================
if __name__ == "__main__":
    if not TOKEN:
        print("Критична помилка: змінна оточення BOT_TOKEN не встановлена.")
        sys.exit(1)
    if ADMIN_IDS[0] == 0:
        print("Попередження: Змінна оточення ADMIN1_ID не встановлена або дорівнює 0. Сповіщення адміністратора не працюватимуть.")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
