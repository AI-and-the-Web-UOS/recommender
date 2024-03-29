import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Tags, Links, Ratings, User
from datetime import datetime

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

    if Tags.query.count() == 0:
        # read tags from csv
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        movie_id = row[1]
                        tag = row[2]
                        timestamp = datetime.utcfromtimestamp(float(row[3]))
                        tag = Tags(user_id=user_id, movie_id=movie_id, tag=tag, timestamp=timestamp)
                        
                        # check if user_id exists in db, if not create user
                        if User.query.filter_by(id=user_id).count() == 0:
                            print(f"User does not exist, adding user with id {user_id}")
                            user = User(id=user_id, username=user_id, )
                            db.session.add(user)
                        
                        db.session.add(tag)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate tag: " + tag)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")

    if Links.query.count() == 0:
        # read links from csv
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdb_id = row[1]
                        tmdb_id = row[2]
                        link = Links(movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id)
                        db.session.add(link)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate link: " + imdb_id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " links read")

    if Ratings.query.count() == 0:
        # read ratings from csv
        with open('data/ratings_full.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        movie_id = row[1]
                        rating = row[2]
                        timestamp = datetime.utcfromtimestamp(float(row[3]))
                        # check if user_id exists in db, if not create user
                        if User.query.filter_by(id=user_id).count() == 0:
                            print(f"User does not exist, adding user with id {user_id}")
                            user = User(id=user_id, username=user_id, )
                            db.session.add(user)

                        rating = Ratings(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)
                        db.session.add(rating)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate rating: " + rating)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")
