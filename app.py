from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_session import Session
from models import db, User, Movie, MovieGenre, Ratings, Tags
from read_data import check_and_read_data
from database import get_user_movie_rating
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from sqlalchemy.sql import not_, exists
from sqlalchemy.orm import aliased
from sqlalchemy import func
from algorithm import find_similar_movies


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

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='ai.and.the.web@gmail.com',
    MAIL_PASSWORD=''
)

mail = Mail(app)
sess = Session()  # initialize Flask-Session

check_and_read_data(db)


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')


def send_mail(email, reset_link):
    try:
        msg = Message("Reset password for MovieMinds",
                      sender='ai.and.the.web@gmail.com',
                      recipients=[email])
        msg.body = f"Click this link to reset you password: {reset_link}"
        mail.send(msg)
        return 'Mail sent!'
    except Exception as e:
        return str(e)


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
            return redirect(url_for('home'))
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

        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']

        user = User.query.filter_by(username=username).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiration = datetime.utcnow() + timedelta(hours=2)
            db.session.commit()

            reset_link = url_for('reset_password', token=token, _external=True)

            print(send_mail(username, reset_link))

            flash('Ein Link zum Zurücksetzen des Passworts wurde an Ihre E-Mail-Adresse gesendet.', 'info')
            return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if user:
        if request.method == 'POST':
            password1 = request.form['password1']
            password2 = request.form['password2']

            if password1 == password2:
                hashed_password = generate_password_hash(password1, method='sha256')

                user.password = hashed_password
                user.reset_token = None
                user.reset_token_expiration = None
                db.session.commit()

                flash('Ihr Passwort wurde erfolgreich zurückgesetzt.', 'success')
                return redirect(url_for('login'))

        return render_template('reset_password.html', token=token)
    else:
        flash('Der Link zum Zurücksetzen des Passworts ist ungültig oder abgelaufen.', 'danger')
        return redirect(url_for('login'))


@app.route("/")
def home():
    if 'user_id' in session:

        db_session = db.session

        movie_ids, movie_list = find_similar_movies(session['user_id'])
        if len(movie_ids) > 0:
            movies = db_session.query(
                Movie.title,
                func.count(Ratings.id).label('rating_count'),
                Movie.id,
                func.round(func.avg(Ratings.rating), 1).label('rating_average')
            ).filter(
                Movie.id.in_(movie_ids)
            ).join(
                Ratings, Movie.id == Ratings.movie_id
            ).group_by(
                Movie.title
            ).order_by(
                func.count(Ratings.id).desc()
            ).all()
        else:
            movies = db_session.query(
                Movie.title,
                func.count(Ratings.id).label('rating_count'),
                Movie.id,
                func.round(func.avg(Ratings.rating), 1).label('rating_average')
            ).join(
                Ratings, Movie.id == Ratings.movie_id
            ).group_by(
                Movie.title
            ).order_by(
                func.count(Ratings.id).desc()
            ).limit(30).all()

        genres = ['Adventure', 'Animation', 'Children', 'Comedy', 'Fantasy', 'Romance', 'Drama', 'Action', 'Crime',
                  'Thriller', 'Horror', 'Mystery', 'Sci-Fi', 'War', 'Musical', 'Documentary', 'IMAX', 'Western',
                  'Film-Noir', '(no genres listed)']

        movies_by_genre = {}

        for genre in genres:
            movies_by_genre[genre] = db_session.query(
                Movie.title,
                func.count(Ratings.id).label('rating_count'),
                Movie.id,
                func.round(func.avg(Ratings.rating), 1).label('rating_average')
            ).join(
                MovieGenre, Movie.id == MovieGenre.movie_id
            ).join(
                Ratings, Movie.id == Ratings.movie_id
            ).filter(
                MovieGenre.genre == genre
            ).group_by(
                Movie.title
            ).order_by(
                func.count(Ratings.id).desc()
            ).limit(12).all()

            movies_by_genre[genre] = [movie for movie in movies_by_genre[genre] if movie[2] not in movie_list]

        return render_template('home.html', movies=movies, moviesByGenre=movies_by_genre,
                               firstName=session['first_name'], lastName=session['last_name'])
    else:
        return redirect(url_for('login'))


@app.route("/movie/<int:movie_id>/rate", methods=['GET', 'POST'])
def rate_movie(movie_id):
    movie = Movie.query.get(movie_id)

    if request.method == 'POST':
        selected_rating = request.form.get('selected_rating')
        user_id = session['user_id']

        new_rating = Ratings(movie_id=movie_id, user_id=user_id, rating=float(selected_rating))
        db.session.add(new_rating)
        db.session.commit()

    movie_links = movie.links

    user_rating = get_user_movie_rating(user_id=session["user_id"], movie_id=movie_id)

    if not movie:
        return render_template('home.html', error_message='Movie not found')

    if user_rating:
        return render_template('rate_movie.html', movie=movie, links=movie_links[0], rating=user_rating.rating)
    else:
        return render_template('rate_movie.html', movie=movie, links=movie_links[0])


@app.route("/movies", methods=['GET', 'POST'])
def movies():
    if 'user_id' in session:

        if request.method == 'POST':
            movie_id = request.form['movie_id']
            rating = request.form['rating']

            user_id = session['user_id']

            new_rating = Ratings(movie_id=movie_id, user_id=user_id, rating=rating, timestamp=datetime.utcnow())

            db.session.add(new_rating)
            db.session.commit()

        user_id = session['user_id']

        movie_ratings = aliased(Ratings)
        movies = aliased(Movie)

        rated_movies = (
            db.session.query(movies, movie_ratings.rating)
            .join(movie_ratings, movies.id == movie_ratings.movie_id)
            .filter(movie_ratings.user_id == user_id)
            .all()
        )

        return render_template('movies.html', movies=rated_movies, firstName=session['first_name'],
                               lastName=session['last_name'])
    else:
        return redirect(url_for('login'))


# Start development web server
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    sess.init_app(app)
    app.run(port=5000, debug=True)
