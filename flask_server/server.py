from flask import Flask

app = Flask(__name__)


@app.route("/pibubpi", methods=["GET"])
def say_hello():
    return 'Hello LOOOOOYD'

@app.route("/", methods=["GET"])
def say_stop():
    return 'stop flooding boy'




if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
