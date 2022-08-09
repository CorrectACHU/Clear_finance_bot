import json
import datetime

def get_user(message):
    user = {'id': message.from_user.id, 'username': message.from_user.username, 'datetime':datetime.datetime.now()}
    return user

