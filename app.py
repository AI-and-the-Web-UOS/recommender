from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template('login.html')


@app.route("/home", methods=["POST"])
def go_home():
    return render_template('home.html')


app.run(debug=True)
