import telebot
import pymongo
import json
import os
import bson

from dotenv import load_dotenv

from services.services import get_user, markup_main_menu, markup_back, send_and_go_next, wrong_message
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

# Create categories collection
categories_db = current_db['categories']
basic_categories = json.loads(os.getenv('CATEGORIES'))

if not [i for i in categories_db.find()]:
    ins_result = categories_db.insert_many(basic_categories)
    print(ins_result.inserted_ids)

# Create users collection
users_db = current_db['users']

# Create expenses collection
expenses_db = current_db['expenses']


###############################################################


# LOGIC
@bot.message_handler(commands=['start'])
def start(message):
    current_category = {}
    expense = {}
    expenses = []

    # CATCH COMMANDS FROM MAIN MENU
    def step1(message):
        if message.text == 'Информация':
            send_and_go_next(bot, message, markup_main_menu(),
                             'Этот бот может записывать твои расходы!\n'
                             'Чтобы записать свой расход -\n'
                             'напиши его в формате - \n<b>{<u>сумма без знаков</u>}{<u>категория трат</u>}</b>\n'
                             'Например:<b>"2 такси"</b>\n'
                             'Добавить, удалить или обновить категорию ты можешь с помощью раздела "Мои категории"\n',
                             step1)
        elif message.text == 'Мои категории':
            send_and_go_next(bot, message, categories_markup(message, categories_db, add_button=True),
                             'Твои категории', category1)
        elif message.text == 'Расходы':
            send_and_go_next(bot, message, expenses_markup_main_menu(), 'Выбери действие', expenses_menu1)
        else:
            wrong_message(message, bot, markup_main_menu(), step1)

    # CATCH COMMANDS FROM CATEGORIES MENU
    def category1(message):
        nonlocal current_category
        categories = get_categories(message, categories_db)
        if message.text == 'Назад 🔙':
            send_and_go_next(bot, message, markup_main_menu(), "Выбери что-нибудь еще :)", step1)

        elif message.text == 'Добавить категорию':
            send_and_go_next(bot, message, markup_back(), 'Как будет называться категория?', add_category1)

        elif message.text.lower() in [i['title'] for i in categories]:

            for category in categories:
                current_category = category
                if message.text == f'{category["title"]}' and category['allow'] == message.from_user.id:
                    send_and_go_next(bot, message, category_markup(),
                                     f'Категория: {category["title"].upper()}, выбери действие', category2)
                    break
                elif message.text == f'{category["title"]}':
                    send_and_go_next(bot, message, markup_back(),
                                     f'Категория: {category["title"].upper()}', category2)
                    break

        else:
            wrong_message(
                message, bot, categories_markup(message, categories_db, add_button=True), category1
            )

    # CATCH COMMANDS FROM SOLO CATEGORY MENU
    def category2(message):
        nonlocal current_category
        if message.text == 'Назад 🔙':
            markup = categories_markup(message, categories_db, add_button=True)
            send_and_go_next(bot, message, markup, "Твои категории", category1)
        elif message.text == 'Удалить категорию':
            category = current_category
            categories_db.delete_one({'_id': category['_id']})
            send_and_go_next(bot, message, markup_main_menu(), f'Категория "{category["title"]}" была удалена', step1)
        elif message.text == 'Изменить имя категории':
            send_and_go_next(bot, message, markup_back(), 'Требуется ввести название для новой категории',
                             update_category)
        else:
            wrong_message(message, bot, categories_markup(message, categories_db, add_button=True), category2)

    # CATCH TEXT OR BACK FUNCTION FROM ADD CATEGORY MENU
    def add_category1(message):
        if message.text == "Назад 🔙":
            markup = categories_markup(message, categories_db, add_button=True)
            send_and_go_next(bot, message, markup, "Твои категории", category1)
        else:
            try:
                categories_db.insert_one({'title': message.text.lower(), 'allow': message.from_user.id})
                send_and_go_next(bot, message, markup_main_menu(), f'Категория "{message.text.upper()}" создана!',
                                 step1)
            except:
                send_and_go_next(bot, message, markup_back(), f'Категория "{message.text.upper()}" уже существует!',
                                 add_category1)

    # CATCH TEXT OR BACK FUNCTION FROM UPDATE CATEGORY MENU
    def update_category(message):
        nonlocal current_category
        category = current_category
        old_title = category['title']
        if message.text == "Назад 🔙":
            send_and_go_next(bot, message, category_markup(), "Твои категории", category2)
        else:
            categories_db.update_one({'_id': category['_id']}, {"$set": {'title': message.text.lower()}})
            send_and_go_next(
                bot, message, markup_main_menu(), f'Категория "{old_title}" изменена на "{message.text.upper()}"!',
                step1
            )

    # CATCH COMMANDS FROM EXPENSES_MENU
    def expenses_menu1(message):
        nonlocal expenses
        if message.text == "Назад 🔙":
            send_and_go_next(bot, message, markup_main_menu(), "Выбери что-нибудь еще:)", step1)
        elif message.text == 'Добавить расход':
            send_and_go_next(bot, message, expense_markup_create(), 'Введи сумму, можно вписать вручную',
                             add_expense1)
        elif message.text == 'Посмотреть мои траты':
            expenses = get_expenses_with_categories(message, expenses_db, categories_db)
            send_and_go_next(bot, message, expense_markup_show(expenses), "Твои траты", show_expenses)

    # CATCH COMMANDS FROM EXPENSE MAIN MENU
    def add_expense1(message):
        nonlocal expense
        if message.text == "Назад 🔙":
            send_and_go_next(bot, message, expenses_markup_main_menu(), "Выбери действие", expenses_menu1)
        else:
            try:
                markup = categories_markup(message, categories_db, add_button=False)
                expense = expense_constructor(message)
                send_and_go_next(bot, message, markup, 'Выберите категорию', add_expense2)
            except ValueError:
                send_and_go_next(bot, message, expense_markup_create,
                                 'Требуется ввести расход только цифрами!', add_expense1)

    # CATCH COMMANDS FROM ADD EXPENSE IN NUMBERS MENU
    def add_expense2(message):
        nonlocal expense
        categories = get_categories(message, categories_db)
        if message.text == 'Назад 🔙':
            send_and_go_next(bot, message, expense_markup_create(), "Выбери действие", add_expense1)
        else:
            category = [i for i in categories if i['title'] == message.text.lower()]
            if category:
                expense['category'] = bson.ObjectId(category[0]['_id'])
                send_and_go_next(bot, message, expense_markup_comment(), "Если нужно, напиши коментарий", add_expense3)

    # CATCH COMMANDS FROM ADD EXPENSE IN CATEGORIES MENU
    def add_expense3(message):
        nonlocal expenses
        if message.text == 'Назад 🔙':
            markup = categories_markup(message, categories_db, add_button=False)
            send_and_go_next(bot, message, markup, "Выбери действие", add_expense2)
        elif message.text == 'Без комментариев':
            expense['comment'] = 'empty'
            expenses_db.insert_one(expense)
            send_and_go_next(bot, message, expenses_markup_main_menu(),
                             f"Расход {expense['amount']}$ "
                             f"{categories_db.find({'_id': expense['category']})[0]['title']} добавлен в базу!",
                             expenses_menu1)
        else:
            expense['comment'] = message.text
            expenses_db.insert_one(expense)
            send_and_go_next(
                bot, message, expenses_markup_main_menu(),
                f"Расход {expense['amount']}$ {categories_db.find({'_id': expense['category']})[0]['title']} "
                f"добавлен в базу!",
                expenses_menu1
            )

    # CATCH COMMANDS FROM EXPENSE MENU FOR SHOW EXPENSES
    def show_expenses(message):
        nonlocal expenses
        nonlocal expense
        if message.text == "Назад 🔙":
            send_and_go_next(bot, message, expenses_markup_main_menu(), "Выбери действие", expenses_menu1)
        else:
            expense = get_expense_from_string(message, expenses)
            send_and_go_next(bot, message, expense_markup_delete(), "Выберите расход", delete_expense)

    # CATCH COMMANDS FROM SHOW EXPENSES FOR DELETE EXPENSE
    def delete_expense(message):
        nonlocal expense
        if message.text == "Назад 🔙":
            send_and_go_next(bot, message, expense_markup_show(expenses), "Твои траты", show_expenses)
        else:
            expense_ID = expense['_id']
            expenses_db.delete_one({'_id': expense_ID})
            send_and_go_next(
                bot, message, expenses_markup_main_menu(),
                f"Расход <b>{expense['amount']}$, "
                f"{expense['category']}</b> от "
                f"<b>{expense['datetime']}</b> удален!",
                expenses_menu1
            )

    markup = markup_main_menu()

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
