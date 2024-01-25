from math import sqrt
from database import get_matched_movies, get_user_ratings

def extract_latest_movies(movie_dict, number_of_movies=None):
    """
    Extracts the latest 10 movies' IDs and ratings from a movie dictionary sorted by Unix epoch time timestamps.

    Args:
        movie_dict (dict): A dictionary containing movie information.

    Returns:
        list: A list of tuples containing the movie IDs and ratings of the latest 10 movies.
    """
    # Sort movies by Unix epoch time timestamps in descending order
    movies_sorted = sorted(movie_dict['Movies'], key=lambda x: x['timestamp'])

    if number_of_movies is None:
        number_of_movies = len(movies_sorted)

    # Extract the latest 10 movies' IDs and ratings
    latest_movies = [(movie['movie_id'], movie['user_rating']) for movie in movies_sorted[:number_of_movies]]

    return latest_movies

def calculate_cosine_similarity(list1, list2):
    """
    Calculates the cosine similarity between two lists of movies.

    Args:
        list1 (list): The first list of movies, where each movie is represented as a tuple (movie_id, rating).
        list2 (list): The second list of movies, where each movie is represented as a tuple (movie_id, rating).

    Returns:
        float: The cosine similarity between the two lists of movies.
    """
    # Convert lists into dictionaries for easier lookup
    dict1 = {movie[0]: movie[1] for movie in list1}
    dict2 = {movie[0]: movie[1] for movie in list2}

    # Find common movies
    common_movies = set(dict1.keys()).intersection(set(dict2.keys()))

    # Calculate the dot product and the magnitudes
    dot_product = sum(dict1[movie] * dict2[movie] for movie in common_movies)
    magnitude1 = sqrt(sum([dict1[movie]**2 for movie in common_movies]))
    magnitude2 = sqrt(sum([dict2[movie]**2 for movie in common_movies]))

    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    # Calculate cosine similarity
    cosine_similarity = dot_product / (magnitude1 * magnitude2)
    return cosine_similarity

def find_most_similar_users(similarity_dict):
    """
    Finds the users with the highest similarity score in the given similarity dictionary.

    Args:
        similarity_dict (dict): A dictionary containing user similarity scores.

    Returns:
        list: A list of users with the highest similarity score.
    """
    # Sort the dictionary by similarity in descending order
    sorted_similarity = sorted(similarity_dict.items(), key=lambda x: x[1], reverse=True)

    # Get the highest similarity score
    highest_similarity = sorted_similarity[0][1] if sorted_similarity else None

    # Find all users with the highest similarity score
    most_similar_users = [user for user, similarity in sorted_similarity if similarity == highest_similarity]

    return most_similar_users

def top_rated_movies(users, excluded_movie_ids, top_n=12):
    """
    Returns a list of top-rated movies based on the average ratings from user data.

    Parameters:
    - users (list): A list of user data, where each user is a dictionary containing a 'movies' key.
                    Each 'movies' key contains a list of tuples representing movie ratings.
                    Each tuple contains a movie ID and a rating.
    - excluded_movie_ids (list): A list of movie IDs to be excluded from the top-rated movies.
    - top_n (int): The number of top-rated movies to be returned. Default is 12.

    Returns:
    - list: A list of movie IDs representing the top-rated movies.
    """
    movie_ratings = {}

    # Aggregate ratings for each movie
    for user in users:
        for movie in user['movies']:
            movie_id, rating = movie
            if movie_id not in movie_ratings:
                movie_ratings[movie_id] = []
            movie_ratings[movie_id].append(rating)

    # Calculate average rating for each movie
    avg_ratings = {movie_id: sum(ratings) / len(ratings) for movie_id, ratings in movie_ratings.items()}

    # Filter out movies that are in the excluded list
    avg_ratings = {movie_id: rating for movie_id, rating in avg_ratings.items() if movie_id not in excluded_movie_ids}

    # Sort movies by average rating and select top N
    top_movies = sorted(avg_ratings.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [movie_id for movie_id, _ in top_movies]

def find_similar_movies(target_user_id):
    """
    Finds similar movies for a given target user.

    Parameters:
    target_user_id (int): The ID of the target user.

    Returns:
    list: A list of top rated movies recommended for the target user.
    """
    overlapping_users = get_matched_movies(target_user_id, 10).json
    user_ratings = get_user_ratings(target_user_id).json

    movie_list = extract_latest_movies(user_ratings, 10)
    movie_id_list = [movie[0] for movie in movie_list]

    user_similarity = {}
    for user in overlapping_users:
        same_movies = [data for data in user['movies'] if data[0] in movie_id_list]
        similarity = calculate_cosine_similarity(movie_list, same_movies)
        user_similarity[user['userID']] = similarity
    
    similar_user = find_most_similar_users(user_similarity)
    similar_overlapping_users = [user for user in overlapping_users if user['userID'] in similar_user]
    top_movies = top_rated_movies(similar_overlapping_users, movie_id_list)

    return top_movies, [movie[0] for movie in extract_latest_movies(user_ratings)]