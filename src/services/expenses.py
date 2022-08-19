import datetime

from telebot import types

from .services import back_button


def get_expenses(message, collection):
    expenses = collection.find({'user': message.from_user.id})
    return expenses


def expenses_markup_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Добавить расход')
    item2 = types.KeyboardButton('Посмотреть мои траты')
    item3 = back_button()
    markup.add(item1, item2, item3)
    return markup


def expense_markup_create():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = '1'
    items = [str(i * 2) for i in range(1, 8)]
    markup.add(item1, *items, back_button())
    return markup


def expense_markup_comment():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Без комментариев')
    markup.add(item1, back_button())
    return markup


def expense_constructor(message):
    amount = int(message.text)
    expense = {'user': message.from_user.id, 'amount': amount, 'datetime': datetime.datetime.now()}
    return expense
