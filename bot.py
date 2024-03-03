import asyncio
import os
import emoji
import requests
from dotenv import load_dotenv
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    CallbackContext

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
TARGET_USER_ID = os.getenv('TARGET_USER_ID')
BOT_USERNAME = os.getenv('BOT_USERNAME')
# Dictionary to store registration data (use a persistent storage instead for real applications)
registrations = {'Начинащие': set(), 'Продолжающие': set()}
# Password for manual list clearing (replace with your desired password)
CLEAR_PASSWORD = "your_password"
# Custom data
subject_for_beginner = ''
subject_for_pro = ''
time_for_beginner = ''
time_for_pro = ''
next_friday = ''


# Helper functions
def clear_registrations():
    global registrations
    registrations = {'Начинащие': set(), 'Продолжающие': set()}


def send_message(chat_id, text):
    """Sends a message to the specified chat ID."""
    try:
        url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
        print(requests.get(url).json())
    except Exception as e:
        print(f"Error sending message: {e}")


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        return
    await admin_menu_command(update, context)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'beginner':
        asyncio.create_task(sign_up_beginner_command(update, context))
    elif query.data == 'pro':
        asyncio.create_task(sign_up_pro_command(update, context))
    elif query.data == 'cancel':
        asyncio.create_task(cancel_command(update, context))
    elif query.data == 'closest_meeting':
        asyncio.create_task(closest_meeting(update, context))
    elif query.data == 'check_assignments':
        asyncio.create_task(check_assignments(update, context))
    elif query.data == 'menu':
        asyncio.create_task(menu_command(update, context))
    elif query.data == 'change_subject_for_beginner':
        asyncio.create_task(change_subject_for_beginner(update, context))
    elif query.data == 'change_subject_for_pro':
        asyncio.create_task(change_subject_for_pro(update, context))
    elif query.data == 'change_time_for_beginner':
        asyncio.create_task(change_time_for_beginner(update, context))
    elif query.data == 'change_time_for_pro':
        asyncio.create_task(change_time_for_pro(update, context))
    elif query.data == 'change_next_friday':
        asyncio.create_task(change_next_friday(update, context))
    elif query.data == 'admin_menu':
        asyncio.create_task(admin_menu_command(update, context))
    else:
        await update.message.reply_text("Такого варианта нету, выберите снова.")


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ],
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Запись для начинающих", callback_data="beginner")
        ],
        [
            InlineKeyboardButton("Запись для продолжающих", callback_data="pro")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"""
Привет!{emoji.emojize(':waving_hand:')}

Я бот-помошник для записи в разговорный клуб школы 
<b>"Nisam stranac"</b>.

* Разговорники проходит каждую пятницу.{emoji.emojize(':spiral_calendar:')}
* Адрес: Футошка 1а, 5 этаж, офис 510.{emoji.emojize(':round_pushpin:')}\n
Для управления ботом используйте кнопки, расположенные ниже.\n
Кнопка <b>"Следующая встреча"</b> - расскажет вам о темах будущих разговорников.\n
Друзья, если у вас не получается прийти, пожалуйста отмените свою запись.""", reply_markup=reply_markup,
        parse_mode=ParseMode.HTML)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Проверить запись", callback_data="check_assignments")
        ],
        [
            InlineKeyboardButton("Запись для начинающих", callback_data="beginner")
        ],
        [
            InlineKeyboardButton("Запись для продолжающих", callback_data="pro")
        ],
        [
            InlineKeyboardButton("Отменить запись", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Меню", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Меню", reply_markup=reply_markup)


async def closest_meeting(update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /when_is_closest_meeting command."""
    keyboard = [
        [
            InlineKeyboardButton("Запись для начинающих", callback_data="beginner")
        ],
        [
            InlineKeyboardButton("Запись для продолжающих", callback_data="pro")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    next_date = next_friday
    if update.message:
        await update.message.reply_text(text=
                                        f"""Следующая встреча в  <b>пятницу</b>, <b>{next_date}</b>.\n
Тема для начинающих в <b>{time_for_beginner}</b>:
{subject_for_beginner}\n
Тема для продолжающих в <b>{time_for_pro}</b>:
{subject_for_pro}""", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.callback_query.edit_message_text(
            text=
            f"""Следующая встреча в <b>пятницу</b>, <b>{next_date}</b>.\n
Тема для начинающих в <b>{time_for_beginner}</b>:
{subject_for_beginner}\n
Тема для продолжающих в <b>{time_for_pro}</b>:
{subject_for_pro}""", reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def sign_up_beginner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /signup_beginner command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    next_date = next_friday
    keyboard = [
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_name_n_tag in registrations['Начинащие']:
        if update.message:
            await update.message.reply_text("Вы уже зарегистрированы на встречу для начинающих.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы уже зарегистрированы на встречу для начинающих.",
                                                          reply_markup=reply_markup)
    elif user_name_n_tag in registrations['Продолжающие']:
        if update.message:
            await update.message.reply_text("Вы уже зарегистрированы на встречу для продолжающих.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы уже зарегистрированы на встречу для продолжающих.",
                                                          reply_markup=reply_markup)
    elif registrations['Начинащие'].__len__() >= 11:
        if update.message:
            await update.message.reply_text("Встречи для начинающих заполнены.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Встречи для начинающих заполнены.",
                                                          reply_markup=reply_markup)
    else:
        registrations['Начинащие'].add(user_name_n_tag)
        if update.message:
            await update.message.reply_text(
                f"""Вы успешно зарегистрированы на встречу для начинающих на 
{next_date} в {time_for_beginner}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                ))
            # Send notification to the target user
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - записался(ась) на встречу для новичков {next_date}")
        else:
            await update.callback_query.edit_message_text(
                f"""Вы успешно зарегистрированы на встречу для начинающих на 
{next_date} в {time_for_beginner}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                )
            )
            # Send notification to the target user
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - записался(ась) на встречу для новичков {next_date}")


async def sign_up_pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /signup_pro command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    next_date = next_friday
    keyboard = [
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_name_n_tag in registrations['Продолжающие']:
        if update.message:
            await update.message.reply_text("Вы уже зарегистрированы на встречу для продолжающих.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы уже зарегистрированы на встречу для продолжающих.",
                                                          reply_markup=reply_markup)
    elif user_name_n_tag in registrations['Начинащие']:
        if update.message:
            await update.message.reply_text("Вы уже зарегистрированы на встречу для начинающих.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text("Вы уже зарегистрированы на встречу для начинающих.",
                                                          reply_markup=reply_markup)
    elif registrations['Продолжающие'].__len__() >= 11:
        if update.message:
            await update.message.reply_text("Встречи для продолжающих заполнены.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text("Встречи для продолжающих заполнены.",
                                                          reply_markup=reply_markup)
    else:
        registrations['Продолжающие'].add(user_name_n_tag)
        if update.message:
            await update.message.reply_text(
                f"""Вы успешно зарегистрированы на встречу для продолжающих на 
{next_date} в {time_for_pro}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                ))
            # Send notification to the target user
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - записался(ась) на встречу для продолжающих {next_date}")
        else:
            await update.callback_query.edit_message_text(
                f"""Вы успешно зарегистрированы на встречу для продолжающих на 
{next_date} в {time_for_pro}.""",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Отменить запись", callback_data="cancel")],
                     [InlineKeyboardButton("Меню", callback_data="menu")]]
                )
            )
            # Send notification to the target user
            send_message(chat_id=TARGET_USER_ID,
                         text=f"{user_name} - записался(ась) на встречу для продолжающих {next_date}")


async def check_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /check_assignments command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    next_date = next_friday
    keyboard = [
        [
            InlineKeyboardButton("Отменить запись", callback_data="cancel")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    keyboard2 = [
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup2 = InlineKeyboardMarkup(keyboard2)

    is_registered_beginner = user_name_n_tag in registrations['Начинащие']
    is_registered_pro = user_name_n_tag in registrations['Продолжающие']

    if is_registered_beginner and is_registered_pro:
        # User is signed up for both meetings
        if update.message:
            await update.message.reply_text(
                f"Вы записаны на обе встречи в пятницу, {next_date}:\n"
                f"* Для начинающих в {time_for_beginner}.\n"
                f"* Для продолжающих в {time_for_pro}.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"Вы записаны на обе встречи в пятницу, {next_date}:\n"
                f"* Для начинающих в {time_for_beginner}.\n"
                f"* Для продолжающих в {time_for_pro}.", reply_markup=reply_markup)
    elif is_registered_beginner:
        # User is only signed up for beginner meeting
        if update.message:
            await update.message.reply_text(
                f"Вы записались на встречу для начинающих в пятницу, {next_date} в {time_for_beginner}.",
                reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"Вы записались на встречу для начинающих в пятницу, {next_date} в {time_for_beginner}.",
                reply_markup=reply_markup)
    elif is_registered_pro:
        # User is only signed up for pro meeting
        if update.message:
            await update.message.reply_text(
                f"Вы записались на встречу для продолжающих в пятницу, {next_date} в {time_for_pro}.",
                reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                f"Вы записались на встречу для продолжающих в пятницу, {next_date} в {time_for_pro}.",
                reply_markup=reply_markup)
    else:
        # User is not signed up for any meetings
        if update.message:
            await update.message.reply_text("Вы не записаны ни на одну встречу.", reply_markup=reply_markup2)
        else:
            await update.callback_query.edit_message_text("Вы не записаны ни на одну встречу.",
                                                          reply_markup=reply_markup2)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /cancel command."""
    user_name = update.effective_user.full_name
    user_tag = update.effective_user.username
    user_name_n_tag = f"{user_name}, @{user_tag}"
    next_date = next_friday
    keyboard = [
        [
            InlineKeyboardButton("Следующая встреча", callback_data="closest_meeting")
        ],
        [
            InlineKeyboardButton("Меню", callback_data="menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_name_n_tag in registrations['Начинащие']:
        registrations['Начинащие'].remove(user_name_n_tag)
        send_message(chat_id=TARGET_USER_ID,
                     text=f"{user_name} - отменил(а) запись на встречу для начинающих {next_date}")
        if update.message:
            await update.message.reply_text("Вы отменили запись на встречу для начинающих.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы отменили запись на встречу для начинающих.",
                                                          reply_markup=reply_markup)
    elif user_name_n_tag in registrations['Продолжающие']:
        registrations['Продолжающие'].remove(user_name_n_tag)
        send_message(chat_id=TARGET_USER_ID,
                     text=f"{user_name} - отменил(а) запись на встречу для продолжающих {next_date}")
        if update.message:
            await update.message.reply_text("Вы отменили запись на встречу для продолжающих.",
                                            reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы отменили запись на встречу для продолжающих.",
                                                          reply_markup=reply_markup)
    else:
        if update.message:
            await update.message.reply_text("Вы не записаны ни на одну встречу.", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text="Вы не записаны ни на одну встречу.",
                                                          reply_markup=reply_markup)


# Admin commands
async def admin_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /admin_menu command."""
    keyboard = [
        [
            InlineKeyboardButton("Изменить тему для начинающих", callback_data="change_subject_for_beginner"),
        ],
        [
            InlineKeyboardButton("Изменить тему для продолжающих", callback_data="change_subject_for_pro"),
        ],
        [
            InlineKeyboardButton("Изменить время для начинающих", callback_data="change_time_for_beginner"),
        ],
        [
            InlineKeyboardButton("Изменить время для продолжающих", callback_data="change_time_for_pro"),
        ],
        [
            InlineKeyboardButton("Изменить дату", callback_data="change_next_friday"),
        ],
        [
            InlineKeyboardButton("Назад", callback_data="menu")
        ]
    ]
    admin_menu_keyboard = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=admin_menu_keyboard)
    else:
        await update.callback_query.edit_message_text("Выберите действие:", reply_markup=admin_menu_keyboard)
    print('Открыто меню администратора')


async def change_subject_for_beginner(update, context):
    pass


async def save_subject_for_beginner(update, context):
    pass


async def change_subject_for_pro(update, context):
    pass


async def save_subject_for_pro(update, context):
    pass


async def change_time_for_beginner(update, context):
    pass


async def save_time_for_beginner(update, context):
    pass


async def change_time_for_pro(update, context):
    pass


async def save_time_for_pro(update, context):
    pass


async def change_next_friday(update, context):
    pass


async def save_next_friday(update, context):
    pass


# Responses

def handle_response(text: str, context: ContextTypes.DEFAULT_TYPE, update: Update) -> str:
    """Handles the user's request to show the list."""
    processed_text = text.lower()

    if "admin:show list" in processed_text:
        beginners_list: str = "\n".join(registrations["Начинащие"])
        pro_list: str = "\n".join(registrations["Продолжающие"])
        return f"Начинающие:\n{beginners_list}\n\nПродолжающие:\n{pro_list}"
    elif "admin:subject beginner:" in processed_text:
        split_messsage = processed_text.split(":")
        global subject_for_beginner
        subject_for_beginner = split_messsage[2].capitalize()
        return f"Текущая тема для начинающих: {subject_for_beginner}"
    elif "admin:subject pro:" in processed_text:
        split_messsage = processed_text.split(":")
        global subject_for_pro
        subject_for_pro = split_messsage[2].capitalize()
        return f"Текущая тема для продолжающих: {subject_for_pro}"
    elif "admin:time beginner:" in processed_text:
        split_messsage = processed_text.split(":")
        global time_for_beginner
        time_for_beginner = split_messsage[2]
        return f"Текущее время для начинающих: {time_for_beginner}"
    elif "admin:time pro:" in processed_text:
        split_messsage = processed_text.split(":")
        global time_for_pro
        time_for_pro = split_messsage[2]
        return f"Текущее время для продолжающих: {time_for_pro}"
    elif "admin:next friday:" in processed_text:
        split_messsage = processed_text.split(":")
        global next_friday
        next_friday = split_messsage[2]
        return f"Текущая дата: {next_friday}"
    elif "admin:clear list" in processed_text:
        clear_registrations()
        return "Регистрации очищены."
    else:
        return "Я не знаю как на это отвечать."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type} says: '{text}'")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            responce: str = handle_response(new_text, context, update)
        else:
            return
    else:
        responce: str = handle_response(text, context, update)
        print("Registered users:")
        for group, users in registrations.items():
            print(f"- {group}: {', '.join(user.split(', ')[0] for user in users)}")

    print('Bot say: ' + responce)
    await update.message.reply_text(responce)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


if __name__ == '__main__':
    print('Bot starting...')
    application = Application.builder().token(API_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('closest_meeting', closest_meeting))
    application.add_handler(CommandHandler('sign_up_beginner', sign_up_beginner_command))
    application.add_handler(CommandHandler('sign_up_pro', sign_up_pro_command))
    application.add_handler(CommandHandler('check_assignments', check_assignments))
    application.add_handler(CommandHandler('cancel_assignment', cancel_command))
    # Work in progress
    application.add_handler(CommandHandler('admin', admin_command))
    application.add_handler(CommandHandler('change_subject_for_beginner', change_subject_for_beginner))
    application.add_handler(CommandHandler('change_subject_for_pro', change_subject_for_pro))
    application.add_handler(CommandHandler('change_time_for_beginner', change_time_for_beginner))
    application.add_handler(CommandHandler('change_time_for_pro', change_time_for_pro))
    application.add_handler(CommandHandler('change_next_friday', change_next_friday))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # Buttons
    application.add_handler(CallbackQueryHandler(button))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)
    # Polls the bot
    print('Polling...')
    application.run_polling(poll_interval=3)
