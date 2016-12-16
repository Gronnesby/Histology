
import os

from flask import Flask, render_template, url_for
app = Flask(__name__)



@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", title="Home")





if __name__ == "__main__":

    app.debug = True
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000
    app.run(HOST, PORT)
