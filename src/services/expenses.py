import datetime

from telebot import types

from .services import button_back, format_datetime


def expense_constructor(message):
    amount = int(message.text)
    expense = {'user': message.from_user.id, 'amount': amount, 'datetime': format_datetime(datetime.datetime.now())}
    return expense


def get_expense_from_string(message, expenses):
    mess = int(message.text.split()[0][:-1])
    expense = expenses[mess - 1]
    return expense


def get_expenses(message, collection):
    expenses = collection.find({'user': message.from_user.id})
    return expenses


def get_expenses_with_categories(message, collection1, collection2):
    expenses = [i for i in collection1.find({'user': message.from_user.id})]
    for i in expenses:
        i['category'] = collection2.find({'_id': i['category']})[0]['title']
    return expenses


def expenses_markup_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Добавить расход')
    item2 = types.KeyboardButton('Посмотреть мои траты')
    markup.add(item1, item2)
    markup.add(button_back())
    return markup


def expense_markup_create():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = '1'
    items = [str(i * 2) for i in range(1, 8)]
    markup.add(item1, *items)
    markup.add(button_back())
    return markup


def expense_markup_comment():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Без комментариев')
    markup.add(item1, button_back())
    return markup


def expense_markup_show(expenses):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = []
    numb = 1
    for i in expenses:
        items.append(types.KeyboardButton(f"{numb}. {i['amount']}$ {i['category']} : {i['datetime']}"))
        numb += 1
    markup.add(*items)
    markup.add(button_back())
    return markup


def expense_markup_delete():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Удалить расход')
    markup.add(item, button_back())
    return markup
