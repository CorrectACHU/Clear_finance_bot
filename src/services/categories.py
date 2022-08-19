from telebot import types

from .services import back_button


# Get list of categories
def get_categories(message, db):
    categories = [
        i for i in db.find({"$or": [{"allow": "any"}, {"allow": message.from_user.id}]})
    ]
    return categories


def add_category_button():
    item = types.KeyboardButton('Добавить категорию')
    return item


# Get category markup
def categories_markup(message, db, add_button):
    categories = get_categories(message, db)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if add_button:
        items = [types.KeyboardButton(f'{i["title"]}') for i in categories] + [add_category_button()] + [back_button()]
    else:
        items = [types.KeyboardButton(f'{i["title"]}') for i in categories] + [back_button()]
    markup.add(*items)
    return markup


# Get category menu
def category_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Изменить имя категории')
    item2 = types.KeyboardButton('Удалить категорию')
    markup.add(item1, item2, back_button())
    return markup


def show_categories(message, bot, db):
    categories = " \n".join([i['title'].upper() for i in db.find(
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
