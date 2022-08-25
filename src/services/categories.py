from telebot import types

from .services import button_back


# Get list of categories
def get_categories(message, db):
    categories = [
        i for i in db.find({"$or": [{"allow": "any"}, {"allow": message.from_user.id}]})
    ]
    return categories


def button_add_category():
    item = types.KeyboardButton('Добавить категорию')
    return item


# Get category markup
def categories_markup(message, db, add_button):
    categories = get_categories(message, db)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if add_button:
        items = [types.KeyboardButton(f'{i["title"]}') for i in categories] + [button_add_category()]
    else:
        items = [types.KeyboardButton(f'{i["title"]}') for i in categories]
    markup.add(*items)
    markup.add(button_back())
    return markup


# Get category menu
def category_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Изменить имя категории')
    item2 = types.KeyboardButton('Удалить категорию')
    markup.add(item1, item2)
    markup.add(button_back())
    return markup
