import datetime
import telebot
from telebot import types


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Информация')
    item2 = types.KeyboardButton('Мои категории')
    item3 = types.KeyboardButton('Расходы')
    markup.add(item2, item3, item1)
    return markup


def get_user(message):
    user = {'id': message.from_user.id, 'username': message.from_user.username, 'datetime': datetime.datetime.now()}
    return user


def back_button():
    item = telebot.types.KeyboardButton('Назад 🔙')
    return item


def back_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = back_button()
    markup.add(item)
    return markup


def go_back(message, next_message, bot, markup, next_func):
    bot.send_message(message.chat.id, next_message, reply_markup=markup)
    bot.delete_message(message.chat.id, message.message_id)
    bot.register_next_step_handler(message, next_func)


def wrong_message(message, bot, markup, func):
    bot.send_message(message.chat.id, 'Требуется выбрать кнопку!', reply_markup=markup)
    bot.delete_message(message.chat.id, message.message_id)
    bot.register_next_step_handler(message, func)
