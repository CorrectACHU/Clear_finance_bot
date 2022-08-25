def get_expense_from_string(message):
    mess = int(message['text'].split()[0][:-1])
    # expense = expenses[mess - 1]
    return mess


print(get_expense_from_string({'ss': 'asdfad', 'text': '1. 24142j4n21i3n4'}))
