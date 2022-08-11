import telebot
import pymongo
import json
import os

from dotenv import load_dotenv
from telebot import types

from services.services import get_user, get_expense, lower_strip

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


# LOGIC
@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Hello, <b>{message.from_user.first_name} </b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMdYukegN0DKP2EFZROYWiTa4mtytQAAiIAAw9uxy-17_oMMQ834ikE')
    user = get_user(message)
    if not [i for i in users_db.find({'id': user['id']})]:
        ins_result = users_db.insert_one(user)
        print(ins_result.inserted_id)
        printed_mess = f'Вы зарегистрированы, ваш id {user["id"]}\n'
        bot.send_message(message.chat.id, printed_mess, parse_mode='html')
    bot.send_message(message.chat.id, "Напиши /help, чтобы узнать что умеет бот", parse_mode='html')


# LIST OF CATEGORIES VIEW
@bot.message_handler(commands=['categories'])
def show_categories(message):
    categories = " \n".join([i['title'].upper() for i in categories_db.find(
        {"$or": [{"allow": "any"}, {"allow": f"{message.from_user.id}"}]})]
                            )
    bot.send_message(message.chat.id, categories)
    bot.send_message(
        message.chat.id,
        "Ты можешь узнать теги по которым бот понимает\nв какую категорию отнести тот или иной расход\n просто напиши /tags {название категории}"
    )
    bot.send_message(
        message.chat.id,
        "Так же ты можешь добавить свои категории, просто напиши /add_category {Название категории}"
    )


# ADD CATEGORY
@bot.message_handler(commands=['add_category'])
def add_category(message):
    global category
    category = {'title': '', 'tags': '', 'allow': f'{message.from_user.id}'}

    def step1(message):
        category['title'] = message.text.lower().strip()
        try:
            bot.send_message(
                message.chat.id,
                f"Имя вашей категории {message.text}"
            )
            bot.send_message(
                message.chat.id,
                "Напишите минимум 2 тега через запятую по которым вы сможете добавлять в свою котегорию новые траты"
            )
            bot.register_next_step_handler(message, step2)
        except:
            bot.send_message(message.chat.id, 'Напишите название категории')

    def step2(message):
        category['tags'] = message.text.split(",") + [category['title']]
        markup = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton('Да', callback_data='yes')
        item2 = types.InlineKeyboardButton('Нет', callback_data='no')
        markup.add(item1, item2)
        try:
            bot.send_message(
                message.chat.id,
                f"Теги, по которым вы сможете добавлять расходы {category['tags']}"
            )
            bot.send_message(
                message.chat.id,
                f"Категория: {category['title']},\n теги: {category['tags']},\n<b>Вы хотите сохранить эту категорию?</b>",
                reply_markup=markup,
                parse_mode='html'
            )
        except:
            bot.send_message(message.chat.id, 'Напишите теги пример =>\n кофе, круасан, бутерброд')
            bot.register_next_step_handler(message, step2)

    bot.send_message(
        message.chat.id,
        'Сначала я попрошу Вас написать название категории, затем теги по которым бот будет определять в какую категорию добавлять вашу запись'
    )
    bot.send_message(message.chat.id, 'Напишите название категории')
    bot.register_next_step_handler(message, step1)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == 'yes':
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=f"Категория <b>{category['title']}</b> успешно сохранена!",
                parse_mode='html'
            )
            categories_db.insert_one(category)
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=f"Категория <b>{category['title']}</b> не <u>сохранена!</u>",
                parse_mode='html'
            )


# ADD EXPENSE
@bot.message_handler(commands=['add_expense'])
def add_expense(message):
    def step1(message):
        expense = get_expense(message)
        try:
            mess = str(expense["amount"]) + ' ' + expense["category"] + ' добавлено в базу'
            bot.send_message(message.chat.id, mess)
        except:
            mess = expense['exception']
            bot.send_message(message.chat.id, mess)
            bot.register_next_step_handler(message, step1)

    bot.send_message(message.chat.id, "Введите расход")
    bot.register_next_step_handler(message, step1)


# INFO ABOUT PROJECT
@bot.message_handler(commands=['help'])
def list_of_commands(message):
    bot.send_message(
        message.chat.id,
        'Этот бот может записывать твои расходы!\n'
        'Чтобы записать свой расход -\n'
        'напиши его в формате - \n<b>{<u>сумма без знаков</u>}{<u>категория трат</u>}</b>\n'
        'Например:<b>"2 такси"</b>\n'
        'Свои категории ты можешь посмотреть, написав команду /categories\n'
        'Добавить категорию ты можешь с помощью команды /add_category\n',
        parse_mode='html'
    )


bot.polling(none_stop=True)
