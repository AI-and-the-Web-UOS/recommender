from flask import Flask, render_template, request

from flask_user import login_required, UserManager

from models import db, User, Movie, MovieGenre
from read_data import check_and_read_data


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')


@app.route("/")
def login():
    return render_template('login.html')


@app.route("/home", methods=["POST"])
def home():
    email = request.form.get('email')
    password = request.form.get('password')
    form_name = request.form.get('form_name')

    print(f"Received form from {form_name}: {email} & {password}")

    return render_template('home.html')


@app.route("/register")
def register():
    return render_template('register.html')


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
