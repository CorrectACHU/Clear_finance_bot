import telebot

from credentials import bot_id

bot = telebot.TeleBot(bot_id)


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Hello, <b>{message.from_user.first_name} </b>'
    bot.send_message(message.chat.id, mess, parse_mode='html')
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAMdYukegN0DKP2EFZROYWiTa4mtytQAAiIAAw9uxy-17_oMMQ834ikE')


@bot.message_handler(content_types=['sticker'])
def get_user_text(message):
    bot.send_message(message.chat.id, message)


bot.polling(none_stop=True)
