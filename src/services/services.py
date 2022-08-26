import datetime
import telebot
from telebot import types


def markup_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Информация')
    item2 = types.KeyboardButton('Мои категории')
    item3 = types.KeyboardButton('Расходы')
    markup.add(item2, item3, item1)
    return markup


def get_user(message):
    user = {'id': message.from_user.id, 'username': message.from_user.username, 'datetime': datetime.datetime.now()}
    return user


def button_back():
    item = telebot.types.KeyboardButton('Назад 🔙')
    return item


def markup_back():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = button_back()
    markup.add(item)
    return markup


def send_and_go_next(bot, message, markup, text, next_func):
    """This func is receiving as arguments :
    message: Message();
    text : str();
    bot: Telebot();
    markup: RelativeKeyboardMarkup();
    next_func: func();
    draw :markup:, send to chat :text:, delete previous user message and run next step as :next_func:
    """
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)
    bot.delete_message(message.chat.id, message.message_id)
    bot.register_next_step_handler(message, next_func)


def wrong_message(message, bot, markup, func):
    bot.send_message(message.chat.id, 'Требуется выбрать кнопку!', reply_markup=markup)
    bot.delete_message(message.chat.id, message.message_id)
    bot.register_next_step_handler(message, func)


def format_datetime(date):
    date = str(date)
    date = f"{date[-15:-10]} {date[8:10] + '.' + date[5:7] + '.' + date[2:4]}"
    return date

