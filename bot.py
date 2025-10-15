import telebot
import os
from flask import Flask, request

# === 1. Отримуємо токен і адміністраторів ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(os.getenv("8208162262")), int(os.getenv("8411342070"))]  # ID двох адміністраторів
bot = telebot.TeleBot(TOKEN)

# === 2. Flask-сервер для Webhook ===
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    return "Bot is running via webhook", 200


# === 3. Старт та сповіщення адміністратору ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги", "🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")

    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Вітаємо вас у преміум юридичному сервісі.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

    # Сповіщення адміністратору
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, f"Новий користувач натиснув /start: @{message.from_user.username} ({message.chat.id})")


# === 4. Послуги ===

# --- ВИЇЗД ---
@bot.message_handler(func=lambda m: m.text == "ВИЇЗД")
def service_exit(message):
    text = (
        "💳 *Білий квиток: Ваш Шлях до Свободи та Спокою*\n\n"
        "Пропонуємо послугу оформлення *Білого квитка*.\n\n"
        "📌 *Що входить у послугу:*\n"
        "• Допомога в оформленні Білого квитка\n"
        "• Підбір відповідної статті Закону\n"
        "• Офіційне заключення ВЛК\n"
        "• Документальне підтвердження дозволу на виїзд\n"
        "• Повне виключення з військового обліку\n\n"
        "📄 *Документи, які ви отримуєте:*\n"
        "• Тимчасове посвідчення\n"
        "• ВЛК\n"
        "• Довідка на право виїзду\n\n"
        "✅ *Переваги:*\n"
        "• Повна легальність\n"
        "• Швидкість оформлення 14-16 днів\n"
        "• Конфіденційність\n"
        "• Свобода пересування"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("Назад", "💬 Консультація")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


# --- ІНВАЛІДНІСТЬ ---
@bot.message_handler(func=lambda m: m.text == "ІНВАЛІДНІСТЬ")
def service_disability(message):
    text = (
        "♿ *Група Інвалідності: Ваше Право на Захист та Соціальні Гарантії*\n\n"
        "Комплексна послуга з оформлення групи інвалідності (ІІ або ІІІ), що забезпечує "
        "відстрочку від мобілізації та доступ до соціальних виплат.\n\n"
        "📌 *Що входить у послугу:*\n"
        "• Оформлення ІІ або ІІІ групи інвалідності\n"
        "• Підготовка медичної документації\n"
        "• Отримання довідок МСЕК\n"
        "• Визначення терміну інвалідності\n"
        "• Офіційна відстрочка від мобілізації\n"
        "• Повне проведення по базах та реєстрах\n"
        "• Призначення пенсійних виплат\n\n"
        "📄 *Документи, які ви отримуєте:*\n"
        "• ВЛК\n"
        "• Довідку ЕКОПФ (МСЕК)\n"
        "• Право на пенсію\n\n"
        "✅ *Переваги:*\n"
        "• Гарантована відстрочка\n"
        "• Соціальні гарантії\n"
        "• Легальність та прозорість\n"
        "• Швидке оформлення 14-18 днів"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("Назад", "💬 Консультація")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


# --- ВІДТЕРМІНУВАННЯ ---
@bot.message_handler(func=lambda m: m.text == "ВІДТЕРМІНУВАННЯ")
def service_postpone(message):
    text = (
        "⏳ *Відтермінування мобілізації: Легально та Швидко*\n\n"
        "Відстрочка на 1 рік оформлюється по стану здоров'я через ВЛК упродовж 3-5 днів. "
        "Після оформлення ви можете спокійно пересуватися по Україні.\n\n"
        "📌 *Процес отримання:*\n"
        "1️⃣ Підготовка всіх необхідних документів\n"
        "2️⃣ Надсилаємо фото готових документів та фото з бази даних *Оберег*\n\n"
        "📄 *Документи, які ви отримуєте:*\n"
        "• Тимчасове посвідчення\n"
        "• Довідку (відстрочка на рік)\n"
        "• ВЛК\n\n"
        "✅ *Переваги:*\n"
        "• Швидке оформлення (3-5 днів)\n"
        "• Легальність та офіційність документів\n"
        "• Можливість вільного пересування по Україні"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("Назад", "💬 Консультація")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


# --- ЗВІЛЬНЕННЯ ---
@bot.message_handler(func=lambda m: m.text == "ЗВІЛЬНЕННЯ")
def service_release(message):
    text = (
        "🛡️ *Звільнення з ЗСУ: Індивідуальний Підхід та Юридичні Гарантії*\n\n"
        "Індивідуальний підхід до кожного випадку звільнення з лав ЗСУ в рамках чинного законодавства.\n\n"
        "📌 *Покроковий План:*\n"
        "1️⃣ Консультація та аналіз вашого випадку\n"
        "2️⃣ Збір та підготовка документів\n"
        "3️⃣ Юридичний супровід та взаємодія з державними органами\n"
        "4️⃣ Контроль процесу та захист ваших інтересів\n"
        "5️⃣ Отримання наказу про звільнення\n\n"
        "📄 *Документи, які ви отримуєте:*\n"
        "• Повний пакет документів для звільнення\n"
        "• Підтвердження законності звільнення\n\n"
        "✅ *Переваги:*\n"
        "• Індивідуальний підхід\n"
        "• Повний юридичний супровід\n"
        "• Легальність та захист інтересів"
    )
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("Назад", "💬 Консультація")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)


# === 5. Консультація ===
@bot.message_handler(func=lambda m: m.text == "💬 Консультація")
def contact(message):
    bot.send_message(
        message.chat.id,
        "Натисніть, щоб одразу написати юристу:\n👉 [Написати Ковалову](https://t.me/uristcord)",
        parse_mode="Markdown"
    )


# === 6. Повернення назад ===
