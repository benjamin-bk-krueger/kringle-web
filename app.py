from flask import Flask

app = Flask(__name__)


@app.route('/flask/hello')
def hello():
    return '<h1>Hello, World!</h1>'
