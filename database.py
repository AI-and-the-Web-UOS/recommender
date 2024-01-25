from flask import jsonify
from models import db, User, Movie, MovieGenre, Ratings

def get_user_ratings(user_id):
    # Get ratings for the user
    ratings = Ratings.query.filter_by(user_id=user_id).all()

    user_ratings = []
    for rating in ratings:
        movie = rating.movie
        if movie:
            movie_title = movie.title
            movie_id = movie.id
            timestamp = rating.timestamp
            user_ratings.append({'title': movie_title, 'user_rating': rating.rating, 'movie_id': movie_id, 'timestamp': timestamp.timestamp()})
        else:
            return jsonify({'error': 'Movie not found'}), 404

    return jsonify({'Movies': user_ratings})

def get_user_movie_rating(user_id, movie_id):
    rating = Ratings.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    return rating

def get_movie_info(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404

    ratings = [rating.rating for rating in movie.ratings]
    if not ratings:
        return jsonify({'error': 'No ratings available for this movie'}), 404

    average_rating = sum(ratings) / len(ratings)
    number_of_votes = len(ratings)
    movie_info = jsonify({'title': movie.title, 'genres': movie.genres, 'average': average_rating, 'number_of_votes': number_of_votes})

    return movie_info

def get_matched_movies(user_id, number_of_movies, result_limit=30):
    # Get the user's recently watched movies
    user_ratings = Ratings.query.filter_by(user_id=user_id).order_by(Ratings.timestamp.desc()).limit(number_of_movies).all()

    # Get other users who watched the same movies
    matching_users = (
        User.query.join(Ratings, User.id == Ratings.user_id)
        .filter(Ratings.movie_id.in_([r.movie_id for r in user_ratings])) # ratings of the same movies as user_id
        .filter(User.id != user_id) # not the same user as user_id
        .group_by(User.id)
        .order_by(db.func.count().desc()) # order by number of movies overlapping descending order
        .limit(result_limit)  # limit results
        .all()
    )

    # Prepare the result
    result = []
    for matching_user in matching_users:
        matching_user_id = matching_user.id
        matching_user_movies = []

        # Get the movies watched by the matching user that have not been watched by user_id yet
        matching_user_ratings = Ratings.query.filter_by(user_id=matching_user_id).filter(
            Ratings.movie_id.notin_([r.movie_id for r in user_ratings])
        ).all()

        # Populate the matching_user_movies list
        for matching_user_rating in matching_user_ratings:
            movie_id = matching_user_rating.movie_id
            rating = matching_user_rating.rating
            matching_user_movies.append((movie_id, rating))

        # Append the result for the matching user
        result.append({'userID': matching_user_id, 'movies': matching_user_movies})

    return jsonify(result)