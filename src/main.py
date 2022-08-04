import telebot
import os
from dotenv import dotenv_values

config = dotenv_values(".env.example")

bot = telebot.TeleBot(config['BOT_ID'])


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Hello, <b>{message.from_user.first_name} </b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMdYukegN0DKP2EFZROYWiTa4mtytQAAiIAAw9uxy-17_oMMQ834ikE')


@bot.message_handler(content_types=['sticker'])
def get_user_text(message):
    bot.send_message(message.chat.id, message)


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
