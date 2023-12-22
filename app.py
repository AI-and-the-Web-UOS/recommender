from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def login():
    return render_template('login.html')


@app.route("/home", methods=["POST"])
def home():
    email = request.form.get('email')
    password = request.form.get('password')
    form_name = request.form.get('form_name')

    print(f"Received form from {form_name}: {email}, {password}")

    return render_template('home.html')

@app.route("/register")
def register():
    return render_template('register.html')

app.run(debug=True)
