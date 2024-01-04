from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_session import Session
from models import db, User, Movie, MovieGenre
from read_data import check_and_read_data
from werkzeug.security import generate_password_hash, check_password_hash


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'
    SESSION_TYPE = 'filesystem'
    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary

sess = Session()  # initialize Flask-Session


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name

            flash('Login successful', 'success')
            return redirect('/')
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    session.clear()
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, password=hashed_password, first_name=first_name, last_name=last_name)

        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username=username).first()

        session['user_id'] = user.id
        session['username'] = user.username
        session['first_name'] = user.first_name
        session['last_name'] = user.last_name

        return redirect('/')

    return render_template('register.html')


@app.route("/")
def home():

    if 'user_id' in session:

        movies = Movie.query.limit(30).all()

        genres = ['Adventure', 'Animation', 'Children', 'Comedy', 'Fantasy', 'Romance', 'Drama', 'Action', 'Crime',
                  'Thriller', 'Horror', 'Mystery', 'Sci-Fi', 'War', 'Musical', 'Documentary', 'IMAX', 'Western',
                  'Film-Noir', '(no genres listed)']

        movies_by_genre = {}

        for genre in genres:
            movies_by_genre[genre] = Movie.query.filter(Movie.genres.any(MovieGenre.genre == genre)).limit(10).all()

        return render_template('home.html', movies=movies, moviesByGenre=movies_by_genre, firstName=session['first_name'], lastName=session['last_name'])
    else:
        return redirect('/login')


# Start development web server
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    sess.init_app(app)
    app.run(port=5000, debug=True)
