import json
import datetime
import telebot


def get_user(message):
    user = {'id': message.from_user.id, 'username': message.from_user.username, 'datetime': datetime.datetime.now()}
    return user


def get_expense(message):
    mess = message.text.split()
    expense = {"user": message.from_user.id, "expense_datetime": datetime.datetime.now()}
    exception = 'Неправильный формат ввода расходов\nправильный=>{сумма} {категория} =>\nнапример : 4 ресторан'

    try:
        if len(mess) == 2:
            expense['amount'] = int(mess[0])
            expense['category'] = mess[1]
        elif len(mess) > 2:
            expense['amount'] = int(mess[0])
            expense['category'] = " ".join([mess[i] for i in range(1, len(mess))])
        else:
            expense["exception"] = exception
    except:
        expense["exception"] = exception
    return expense


def cancel_button():
    item = telebot.types.InlineKeyboardButton('отмена 🚫', callback_data='cancel')
    return item
