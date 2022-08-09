import telebot
import pymongo
import json
import os

from dotenv import load_dotenv
from services.services import get_user


load_dotenv()
# ENV

# BOT init
bot = telebot.TeleBot(os.getenv('BOT_ID'))
###############################################################
# DB's settings
print(os.getenv('MONGO_USERNAME'))
mongo_username = os.getenv('MONGO_USERNAME')
mongo_pass = os.getenv('MONGO_PASS')
db_client = pymongo.MongoClient(f'mongodb://{mongo_username}:{mongo_pass}@mongo:27017/')
current_db = db_client['tbot_database']

# Create categories
categories = current_db['categories']
print(os.getenv('CATEGORIES'))
basic_ctgrs = json.loads(os.getenv('CATEGORIES'))

if not [i for i in categories.find()]:
    ins_result = categories.insert_many(basic_ctgrs)
    print(ins_result.inserted_ids)

# Create users
users = current_db['users']

# Create expenses
expenses = current_db['expenses']


###############################################################


# LOGIC
@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Hello, <b>{message.from_user.first_name} </b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMdYukegN0DKP2EFZROYWiTa4mtytQAAiIAAw9uxy-17_oMMQ834ikE')
    user = get_user(message)
    if not [i for i in users.find({'id': user['id']})]:
        ins_result = users.insert_one(user)
        print(ins_result.inserted_id)
        printed_mess = f'Вы зарегистрированы, ваш id {user["id"]}'
        bot.send_message(message.chat.id, printed_mess, parse_mode='html')


# @bot.message_handler(commands=['go'])
# def get_user_text(message):
#     username = get_username(message)


@bot.message_handler(commands=['help'])
def list_of_commands(message):
    bot.send_message(
        message.chat.id,
        'Этот бот может записывать твои расходы!\n'
        'Учет ведется в <b>$</b>:)\n'
        'Чтобы записать свой расход -\n'
        'напиши его в формате - \n<b>{<u>сумма без знаков</u>}{<u>категория трат</u>}</b>\n'
        'Например:<b>"2 такси"</b>',
        parse_mode='html'
    )


bot.polling(none_stop=True)
