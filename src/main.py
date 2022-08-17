import telebot
import pymongo
import json
import os

from dotenv import load_dotenv
from telebot import types

from services.services import get_user, get_expense, back_button, main_menu, back_markup, go_back
from services.categories import *

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
basic_ctgrs = json.loads(os.getenv('CATEGORIES'))

if not [i for i in categories_db.find()]:
    ins_result = categories_db.insert_many(basic_ctgrs)
    print(ins_result.inserted_ids)

# Create users
users_db = current_db['users']

# Create expenses
expenses_db = current_db['expenses']

###############################################################

current_category = {}


# LOGIC
@bot.message_handler(commands=['start'])
def start(message):
    # CATCH BUTTONS FROM MAIN MENU
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
            markup = categories_markup(message, categories_db)
            bot.send_message(message.chat.id, 'Твои категории', reply_markup=markup)
            bot.delete_message(message.chat.id, message.message_id)
            bot.register_next_step_handler(message, category1)
        elif message.text == 'Мои траты':
            bot.send_message(message.chat.id, 'Это заглушка')

    # CATCH BUTTONS FROM CATEGORIES MENU
    def category1(message):
        global current_category
        categories = get_categories(message, categories_db)
        if message.text == 'Назад 🔙':
            go_back(message, "Выбери что-нибудь еще :)", markup=main_menu(), bot=bot, next_func=step1)
        elif message.text == 'Добавить категорию':
            markup = back_markup()
            bot.send_message(message.chat.id, 'Как будет называться категория?', reply_markup=markup)
            bot.register_next_step_handler(message, add_category1)

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

    # CATCH BUTTONS FROM SOLO CATEGORY MENU
    def category2(message):
        if message.text == 'Назад 🔙':
            markup = categories_markup(message, categories_db)
            go_back(message, "Твои категории", bot, markup, category1)
        elif message.text == 'Удалить категорию':
            markup = main_menu()
            category = current_category
            categories_db.delete_one({'_id': category['_id']})
            bot.send_message(message.chat.id, f'Категория {category["title"]} была удалена', reply_markup=markup)
            bot.register_next_step_handler(message, step1)
        elif message.text == 'Изменить имя категории':
            markup = back_markup()
            bot.send_message(message.chat.id, 'Новое имя категории', reply_markup=markup)
            bot.register_next_step_handler(message, update_category)

    # CATCH TEXT OR BACK BUTTON FROM ADD CATEGORY MENU
    def add_category1(message):
        if message.text == "Назад 🔙":
            markup = categories_markup(message, categories_db)
            go_back(message, "Твои категории", bot, markup, category1)
        else:
            markup = main_menu()
            categories_db.insert_one({'title': message.text.lower(), 'allow': message.from_user.id})
            go_back(message, f'Категория "{message.text.upper()}" создана!', bot, markup, step1)

    # CATCH TEXT OR BACK BUTTON FROM UPDATE CATEGORY MENU
    def update_category(message):
        category = current_category
        old_title = category['title']
        if message.text == "Назад 🔙":
            markup = category_markup()
            go_back(message, "Твои категории", bot, markup, category2)
        else:
            markup = main_menu()
            categories_db.update_one({'_id': category['_id']}, {"$set": {'title': message.text.lower()}})
            go_back(message, f'Категория "{old_title}" изменена на "{message.text.upper()}"!', bot, markup, step1)

    markup = main_menu()

    bot.send_message(message.chat.id, f'Hello, <b>{message.from_user.first_name} </b>', parse_mode='html')
    user = get_user(message)
    if not [i for i in users_db.find({'id': user['id']})]:
        ins_result = users_db.insert_one(user)
        printed_mess = f'Ну все! теперь ты в базе!'
        bot.send_message(message.chat.id, printed_mess, parse_mode='html')
    bot.send_message(message.chat.id, "Ты можешь посмотреть что может бот в разделе 'информация'", parse_mode='html',
                     reply_markup=markup)
    bot.register_next_step_handler(message, step1)


# # ADD EXPENSE
# @bot.message_handler(commands=['add_expense'])
# def add_expense(message):
#     def step1(message):
#         expense = get_expense(message)
#         try:
#             mess = str(expense["amount"]) + ' ' + expense["category"] + ' добавлено в базу'
#             bot.send_message(message.chat.id, mess)
#         except:
#             mess = expense['exception']
#             bot.send_message(message.chat.id, mess)
#             bot.register_next_step_handler(message, step1)
#
#     bot.send_message(message.chat.id, "Введи расход")
#     bot.register_next_step_handler(message, step1)


bot.polling(none_stop=True)
