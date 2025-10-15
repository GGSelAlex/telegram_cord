import os
import telebot
from telebot import types
from flask import Flask, request

# ====== Конфігурація ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [
    int(os.getenv("ADMIN1_ID", "0")),
    int(os.getenv("ADMIN2_ID", "0"))
]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ====== Головне меню ======
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📋 Запис на консультацію"),
        types.KeyboardButton("📂 Послуги")
    )
    return markup

# ====== Меню послуг ======
def services_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("✈️ Виїзд"),
        types.KeyboardButton("🕓 Відтермінування"),
        types.KeyboardButton("♿ Інвалідність"),
        types.KeyboardButton("📜 Звільнення"),
        types.KeyboardButton("🔙 Назад")
    )
    return markup

# ====== Команда /start ======
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 Вітаємо! Це бот юридичної допомоги для чоловіків.\n\n"
        "Ми надаємо:\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ\n\n"
        "Оберіть потрібну дію 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

    # Повідомлення адміністраторам
    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, f"🆕 Новий користувач запустив бота: @{message.from_user.username} (ID: {message.from_user.id})")

# ====== Обробка головного меню ======
@bot.message_handler(func=lambda msg: msg.text == "📋 Запис на консультацію")
def consultation(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    phone_btn = types.KeyboardButton("📞 Надіслати номер телефону", request_contact=True)
    back_btn = types.KeyboardButton("🔙 Назад")
    markup.add(phone_btn, back_btn)
    bot.send_message(message.chat.id, "Будь ласка, надішліть свій номер телефону, щоб юрист зміг з вами зв’язатися 📲", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone = message.contact.phone_number
    username = message.from_user.username
    user_id = message.from_user.id

    for admin_id in ADMIN_IDS:
        if admin_id != 0:
            bot.send_message(admin_id, f"📞 Новий контакт:\n👤 @{username}\n📱 {phone}\n🆔 {user_id}")

    bot.send_message(message.chat.id, "✅ Дякуємо! Юрист зв’яжеться з вами найближчим часом.", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📂 Послуги")
def show_services(message):
    bot.send_message(message.chat.id, "Оберіть напрям послуги 👇", reply_markup=services_menu())

# ====== ВИЇЗД ======
@bot.message_handler(func=lambda msg: msg.text == "✈️ Виїзд")
def vyizd_info(message):
    text = (
        "✈️ **Виїзд за кордон**\n\n"
        "🧾 *Білий квиток: Ваш шлях до свободи та спокою*\n\n"
        "🔹 Повне звільнення від військового обов’язку.\n"
        "🔹 Офіційне підтвердження права на перетин кордону.\n"
        "🔹 Допомога з отриманням висновку ВЛК.\n"
        "🔹 Повне виключення з військового обліку.\n\n"
        "📄 *Ви отримуєте:*\n"
        "• Тимчасове посвідчення\n"
        "• ВЛК\n"
        "• Довідку на право виїзду за кордон\n\n"
        "🧠 Консультація включена у вартість ✅"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

# ====== ВІДТЕРМІНУВАННЯ ======
@bot.message_handler(func=lambda msg: msg.text == "🕓 Відтермінування")
def vidterminuvannya_info(message):
    text = (
        "🕓 **Відтермінування мобілізації**\n\n"
        "⏳ Оформлення відтермінування на 1 рік за станом здоров’я (через ВЛК).\n"
        "Термін виконання — 3–5 днів.\n\n"
        "📄 *Ви отримуєте:*\n"
        "• Тимчасове посвідчення\n"
        "• Довідку про відтермінування (на 1 рік)\n"
        "• ВЛК\n\n"
        "🧠 Консультація включена ✅"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

# ====== ІНВАЛІДНІСТЬ ======
@bot.message_handler(func=lambda msg: msg.text == "♿ Інвалідність")
def invalidnist_info(message):
    text = (
        "♿ **Оформлення групи інвалідності (II або III)**\n\n"
        "🔹 Офіційна підстава для відстрочки від мобілізації.\n"
        "🔹 Допомога з медичними документами та довідками МСЕК.\n"
        "🔹 Внесення до державних реєстрів.\n\n"
        "📄 *Ви отримуєте:*\n"
        "• Висновок ЛЛК\n"
        "• Довідку ЕКОПФ (МСЕК)\n"
        "• Право на пенсію\n\n"
        "🧠 Консультація включена ✅"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

# ====== ЗВІЛЬНЕННЯ ======
@bot.message_handler(func=lambda msg: msg.text == "📜 Звільнення")
def zvilnennya_info(message):
    text = (
        "📜 **Звільнення з ЗСУ**\n\n"
        "🔹 Повний юридичний супровід звільнення.\n"
        "🔹 Допомога з ВЛК, рапортами, документами та зверненнями.\n"
        "🔹 Індивідуальний підхід до кожного випадку.\n\n"
        "📄 *Ви отримуєте:*\n"
        "• Наказ про звільнення\n"
        "• ВЛК (якщо потрібно)\n"
        "• Повний юридичний супровід\n\n"
        "🧠 Консультація включена ✅"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

# ====== Назад ======
@bot.message_handler(func=lambda msg: msg.text == "🔙 Назад")
def back(message):
    bot.send_message(message.chat.id, "🔙 Повернення в головне меню", reply_markup=main_menu())

# ====== Flask для Render ======
@app.route('/')
def index():
    return "Bot is running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
