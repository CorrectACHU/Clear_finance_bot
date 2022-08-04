from flask import Flask

app = Flask(__name__)


@app.route('/', methods=['GET'])
def say_hello():
    return 'Hello!'


if __name__ == "__main__":
    app.run(port=81, debug=True)
