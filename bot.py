import telebot

# === 1. Твій токен від BotFather ===
TOKEN = "8379715669:AAEXC7_BhlnGZUJw-FMj_hVigoByMPjb9C4"
bot = telebot.TeleBot(TOKEN)

# === 2. Головне меню ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⚖️ Послуги")
    markup.row("🕒 Запис на консультацію")
    markup.row("ℹ️ Про компанію", "💬 Консультація")

    welcome_text = (
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Преміум юридична допомога для військових і цивільних.\n"
        "Оберіть потрібний розділ нижче 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# === 3. Послуги ===
@bot.message_handler(func=lambda m: m.text == "⚖️ Послуги")
def services(message):
    bot.send_message(
        message.chat.id,
        "Ми надаємо:\n\n"
        "🔹 Виїзд за кордон\n"
        "🔹 Відтермінування мобілізації\n"
        "🔹 Отримання інвалідності\n"
        "🔹 Звільнення зі служби в ЗСУ\n\n"
        "🕒 Для запису на консультацію натисніть відповідну кнопку нижче."
    )

# === 4. Запис на консультацію ===
@bot.message_handler(func=lambda m: m.text == "🕒 Запис на консультацію")
def consultation(message):
    contact_btn = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    contact_btn.add(telebot.types.KeyboardButton("📲 Надіслати мій номер телефону", request_contact=True))
    bot.send_message(
        message.chat.id,
        "📞 Для зв’язку з юристом залиште свій номер телефону або натисніть кнопку нижче ⬇️",
        reply_markup=contact_btn
    )

# === 5. Обробка надсилання номера ===
@bot.message_handler(content_types=['contact'])
def contact_received(message):
    contact = message.contact
    name = message.from_user.first_name
    phone = contact.phone_number

    # Повідомлення користувачу
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            text="💬 Написати юристу зараз",
            url="https://t.me/uristcord"  # 🔹 заміни на свій username (без @)
        )
    )
    bot.send_message(
        message.chat.id,
        f"Дякуємо, {name}! ✅\n"
        "Ваш номер отримано. Наш юрист зв’яжеться з вами найближчим часом.\n\n"
        "Або натисніть нижче, щоб написати напряму 👇",
        reply_markup=markup
    )

    # 🔔 Повідомлення адміну (тобі)
    admin_chat_id = 8208162262  # 🔹 заміни на свій ID (дізнай у @userinfobot)
    bot.send_message(
        admin_chat_id,
        f"📩 Новий контакт від {name}\nТелефон: {phone}"
    )

# === 6. Про компанію ===
@bot.message_handler(func=lambda m: m.text == "ℹ️ Про компанію")
def about(message):
    bot.send_message(
        message.chat.id,
        "💼 *Юридичні послуги Kovalova Stanislava*\n\n"
        "Ми працюємо з 2022 року, допомагаючи чоловікам отримати законний захист своїх прав.\n"
        "Наша місія — надати впевненість, спокій і професійну юридичну підтримку у найскладніших життєвих ситуаціях.\n\n"
        "*Юридичні послуги Kovalova Stanislava — ваша впевненість у завтрашньому дні.*",
        parse_mode="Markdown"
    )

# === 7. Консультація ===
@bot.message_handler(func=lambda m: m.text == "💬 Консультація")
def direct_consult(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📲 Написати юристу", url="https://t.me/uristcord"))
    bot.send_message(
        message.chat.id,
        "Щоб отримати консультацію зараз — натисніть кнопку нижче 👇",
        reply_markup=markup
    )

# === 8. Запуск ===
print("Бот запущений. Очікуємо повідомлень...")
bot.polling(none_stop=True)
