import telebot
import pymongo
import json
import os

from dotenv import load_dotenv
from telebot import types

from services.services import get_user, main_menu, back_markup, go_back, wrong_message
from services.categories import *
from services.expenses import *

# ENV
load_dotenv()

# BOT init
bot = telebot.TeleBot(os.getenv('BOT_ID'))
###############################################################
# DB's settings
mongo_username = os.getenv('MONGO_USERNAME')
mongo_pass = os.getenv('MONGO_PASS')
db_client = pymongo.MongoClient(f'mongodb://{mongo_username}:{mongo_pass}@mongo:27017/')
current_db = db_client['tbot_database']

# Create categories
categories_db = current_db['categories']
basic_categories = json.loads(os.getenv('CATEGORIES'))

if not [i for i in categories_db.find()]:
    ins_result = categories_db.insert_many(basic_categories)
    print(ins_result.inserted_ids)

categories_db.create_index('title', unique=True)

# Create users
users_db = current_db['users']

# Create expenses
expenses_db = current_db['expenses']


###############################################################


# LOGIC
@bot.message_handler(commands=['start'])
def start(message):
    current_category = {}
    expense = {}

    # CATCH COMMANDS FROM MAIN MENU
    def step1(message):
        if message.text == 'Информация':
            bot.send_message(
                message.chat.id,
                'Этот бот может записывать твои расходы!\n'
                'Чтобы записать свой расход -\n'
                'напиши его в формате - \n<b>{<u>сумма без знаков</u>}{<u>категория трат</u>}</b>\n'
                'Например:<b>"2 такси"</b>\n'
                'Добавить, удалить или обновить категорию ты можешь с помощью раздела "Мои категории"\n',
                parse_mode='html'
            )
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, step1)
        elif message.text == 'Мои категории':
            markup = categories_markup(message, categories_db, add_button=True)
            bot.send_message(message.chat.id, 'Твои категории', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, category1)
        elif message.text == 'Расходы':
            markup = expenses_markup_main_menu()
            bot.send_message(message.chat.id, 'Выбери действие', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, expenses_menu1)
        else:
            wrong_message(message, bot, main_menu(), step1)

    # CATCH COMMANDS FROM CATEGORIES MENU
    def category1(message):
        nonlocal current_category
        categories = get_categories(message, categories_db)
        if message.text == 'Назад 🔙':
            go_back(message, "Выбери что-нибудь еще :)", markup=main_menu(), bot=bot, next_func=step1)
        elif message.text == 'Добавить категорию':
            markup = back_markup()
            bot.send_message(message.chat.id, 'Как будет называться категория?', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, add_category1)
        elif message.text.lower() in [i['title'] for i in categories]:
            for category in categories:
                if message.text == f'{category["title"]}' and category['allow'] == message.from_user.id:
                    current_category = category
                    markup = category_markup()
                    bot.send_message(
                        message.chat.id,
                        f'Категория: {category["title"].upper()}, выбери действие',
                        reply_markup=markup
                    )
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.register_next_step_handler(message, category2)
                elif message.text == f'{category["title"]}':
                    markup = back_markup()
                    current_category = category
                    bot.send_message(
                        message.chat.id,
                        f'Категория: {category["title"].upper()}',
                        reply_markup=markup
                    )
                    bot.delete_message(message.chat.id, message.message_id)
                    bot.register_next_step_handler(message, category2)
        else:
            wrong_message(
                message, bot, categories_markup(message, categories_db, add_button=True), category1
            )

    # CATCH COMMANDS FROM SOLO CATEGORY MENU
    def category2(message):
        nonlocal current_category
        if message.text == 'Назад 🔙':
            markup = categories_markup(message, categories_db, add_button=True)
            go_back(message, "Твои категории", bot, markup, category1)
        elif message.text == 'Удалить категорию':
            markup = main_menu()
            category = current_category
            categories_db.delete_one({'_id': category['_id']})
            bot.send_message(message.chat.id, f'Категория "{category["title"]}" была удалена', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, step1)
        elif message.text == 'Изменить имя категории':
            markup = back_markup()
            bot.send_message(message.chat.id, 'Требуется ввести название для новой категории', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, update_category)
        else:
            wrong_message(message, bot, categories_markup(message, categories_db, add_button=True), category1)

    # CATCH TEXT OR BACK FUNCTION FROM ADD CATEGORY MENU
    def add_category1(message):
        if message.text == "Назад 🔙":
            markup = categories_markup(message, categories_db, add_button=True)
            go_back(message, "Твои категории", bot, markup, category1)
        else:
            try:
                markup = main_menu()
                categories_db.insert_one({'title': message.text.lower(), 'allow': message.from_user.id})
                go_back(message, f'Категория "{message.text.upper()}" создана!', bot, markup, step1)
            except:
                markup = back_markup()
                go_back(message, f'Категория "{message.text.upper()}" уже существует!', bot, markup, add_category1)

    # CATCH TEXT OR BACK FUNCTION FROM UPDATE CATEGORY MENU
    def update_category(message):
        nonlocal current_category
        category = current_category
        old_title = category['title']
        if message.text == "Назад 🔙":
            markup = category_markup()
            go_back(message, "Твои категории", bot, markup, category2)
        else:
            markup = main_menu()
            update_res = categories_db.update_one({'_id': category['_id']}, {"$set": {'title': message.text.lower()}})
            go_back(
                message,
                f'Категория "{old_title}" изменена на "{message.text.upper()}, {update_res.upserted_id.__str__()}"!',
                bot,
                markup,
                step1
            )

    # CATCH COMMANDS FROM EXPENSES_MENU
    def expenses_menu1(message):
        markup = expenses_markup_main_menu()
        if message.text == "Назад 🔙":
            markup = main_menu()
            go_back(message, "Выбери что-нибудь еще:)", bot, markup, step1)
        elif message.text == 'Добавить расход':
            markup = expense_markup_create()
            bot.send_message(message.chat.id, 'Введи сумму, можно вписать вручную', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, add_expense1)
        elif message.text == 'Посмотреть мои траты':
            bot.send_message(message.chat.id, 'РАБОТАЕТ! ТОЖЕ', reply_markup=markup)
            bot.register_next_step_handler(message, expenses_menu1)

    # CATCH COMMANDS FROM EXPENSE MAIN MENU
    def add_expense1(message):
        nonlocal expense
        if message.text == "Назад 🔙":
            markup = expenses_markup_main_menu()
            go_back(message, "Выбери действие", bot, markup, expenses_menu1)
        else:
            try:
                markup = categories_markup(message, categories_db, add_button=False)
                expense = expense_constructor(message)
                bot.send_message(message.chat.id, 'Выберите категорию', reply_markup=markup)
                bot.register_next_step_handler(message, add_expense2)
            except ValueError:
                markup = expense_markup_create()
                bot.send_message(
                    message.chat.id,
                    'Требуется ввести расход только цифрами!',
                    reply_markup=markup
                )
                bot.delete_message(message.chat.id, message.message_id)
                bot.register_next_step_handler(message, add_expense1)

    # CATCH COMMANDS FROM ADD EXPENSE IN NUMBERS MENU
    def add_expense2(message):
        nonlocal expense
        if message.text == 'Назад 🔙':
            markup = expense_markup_create()
            go_back(message, "Выбери действие", bot, markup, add_expense1)
        else:
            markup = expense_markup_comment()
            expense['category'] = message.text.lower()
            bot.send_message(message.chat.id, "Если нужно, напиши коментарий", reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, add_expense3)

    # CATCH COMMANDS FROM ADD EXPENSE IN CATEGORIES MENU
    def add_expense3(message):
        nonlocal expense
        if message.text == 'Назад 🔙':
            markup = categories_markup(message, categories_db, add_button=False)
            go_back(message, "Выбери действие", bot, markup, add_expense2)
        elif message.text == 'Без комментариев':
            markup = expenses_markup_main_menu()
            expense['comment'] = 'empty'
            bot.send_message(message.chat.id, f"Расход {expense['amount']}$ {expense['category']} добавлен в базу!",
                             reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, expenses_menu1)
        else:
            markup = expenses_markup_main_menu()
            expense['comment'] = message.text
            bot.send_message(message.chat.id, f"Расход {expense['amount']}$ {expense['category']} добавлен в базу!",
                             reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, expenses_menu1)

    markup = main_menu()

    # FIRST START, REGISTRATION USER
    bot.send_message(message.chat.id, f'Hello, <b>{message.from_user.first_name} </b>', parse_mode='html')
    user = get_user(message)
    if not [i for i in users_db.find({'id': user['id']})]:
        users_db.insert_one(user)
        printed_mess = f'Регистрация прошла успешно!'
        bot.send_message(message.chat.id, printed_mess, parse_mode='html')
    bot.send_message(message.chat.id, "Ты можешь посмотреть что может бот в разделе 'информация'", parse_mode='html',
                     reply_markup=markup)
    bot.register_next_step_handler(message, step1)


bot.polling(none_stop=True)
