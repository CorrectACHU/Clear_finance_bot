import telebot
import pymongo
import json
import os

from dotenv import load_dotenv
from telebot import types

from services.services import get_user, get_expense, cancel_button

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
    bot.send_message(message.chat.id, "Используй команду /help, \nчтобы узнать что умеет бот", parse_mode='html')


# LIST OF CATEGORIES VIEW
@bot.message_handler(commands=['categories'])
def show_categories(message):
    categories = " \n".join([i['title'].upper() for i in categories_db.find(
        {"$or": [{"allow": "any"}, {"allow": f"{message.from_user.id}"}]})]
                            )
    bot.send_message(message.chat.id, categories)
    bot.send_message(
        message.chat.id,
        "Ты можешь узнать теги по которым бот понимает\nв какую категорию отнести тот или иной расход\nпросто используй команду /tags"
    )
    bot.send_message(
        message.chat.id,
        "Так же ты можешь добавить свои категории, \nиспользуй команду /add_category"
    )


# SHOW TAGS
@bot.message_handler(commands=['tags'])
def show_category_tags(message):
    categories = [i for i in categories_db.find({"$or": [{"allow": "any"}, {"allow": f"{message.from_user.id}"}]})]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = [types.KeyboardButton(f'{i["title"]}') for i in categories] + [
        cancel_button()]
    markup.add(*items)

    def step1(message):
        for i in categories:
            markup = types.ReplyKeyboardRemove()
            if message.text == "отмена 🚫":
                bot.delete_message(message.chat.id, message.message_id)
                bot.delete_message(message.chat.id, message.message_id - 1)
                bot.send_message(message.chat.id, "Действие отменено", reply_markup=markup)
            elif message.text == f"{i['title']}":
                bot.delete_message(message.chat.id, message.message_id)
                bot.delete_message(message.chat.id, message.message_id - 1)
                bot.send_message(
                    message.chat.id,
                    f"Следующие теги относяться к категории <b>{i['title']}</b> :\n{', '.join(i['tags'])}",
                    parse_mode='html', reply_markup=markup
                )

    bot.send_message(message.chat.id, "Выберите категорию ", reply_markup=markup)
    bot.register_next_step_handler(message, step1)


# ADD CATEGORY
@bot.message_handler(commands=['add_category'])
def add_category(message):
    global category
    category = {'title': '', 'tags': '', 'allow': f'{message.from_user.id}'}
    markup = types.InlineKeyboardMarkup()

    def step1(message):
        nonlocal markup
        category['title'] = message.text.lower().strip()
        try:
            bot.send_message(
                message.chat.id,
                f"Имя категории {message.text}"
            )
            bot.send_message(
                message.chat.id,
                "Напиши тег через запятую по которым ты сможешь добавлять в свою котегорию новые траты",
                reply_markup=markup,
            )
            bot.register_next_step_handler(message, step2)
        except:
            bot.send_message(message.chat.id, 'Напиши название категории')

    def step2(message):
        category['tags'] = message.text.split(",") + [category['title']]
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('Да', callback_data='yes')
        item2 = types.InlineKeyboardButton('Нет', callback_data='no')
        markup.add(item1, item2)
        try:
            bot.send_message(
                message.chat.id,
                f"Теги, по которым ты сможешь добавлять расходы :\n{', '.join(category['tags'])}"
            )
            bot.send_message(
                message.chat.id,
                f"Категория: {category['title']},\nтеги - {','.join(category['tags'])},\n<b>Cохранить эту категорию?</b>",
                reply_markup=markup,
                parse_mode='html'
            )
        except:
            bot.send_message(message.chat.id, 'Напиши теги пример =>\n кофе, круасан, бутерброд')
            bot.register_next_step_handler(message, step2)

    bot.send_message(
        message.chat.id,
        'Сначала напиши название категории, затем теги по которым бот будет определять в какую категорию добавлять запись'
    )
    bot.send_message(message.chat.id, 'Напиши название категории')
    bot.register_next_step_handler(message, step1)


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

    bot.send_message(message.chat.id, "Введи расход")
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


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global category
    if call.message:
        if call.data == 'yes':
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=f"Категория <b>{category['title']}</b> успешно сохранена!",
                parse_mode='html'
            )
            categories_db.insert_one(category)
        elif call.data == 'no':
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=f"Категория <b>{category['title']}</b> не <u>сохранена!</u>",
                parse_mode='html'
            )


bot.polling(none_stop=True)
