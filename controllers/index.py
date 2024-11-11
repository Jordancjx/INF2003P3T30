from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
import config.constants

index_bp = Blueprint('index', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/')


@index_bp.route('/')
def index():
    recommendations = None
    searchQuery = request.args.get("searchName")
    page = request.args.get('page', default=1, type=int)  # Defaults to page 1 if not provided
    per_page = request.args.get('per_page', default=12, type=int)  # Defaults to 12 items per page if not provided

    db = current_app.mongo.db
    user_id = session.get('user_id')

    # Conditional filter for search criteria
    query_filter = {}
    if searchQuery:
        # Apply search filter if searchQuery is not empty
        query_filter = {
            "$or": [
                {"title": {"$regex": searchQuery, "$options": "i"}},
                {"genres": {"$regex": searchQuery, "$options": "i"}},
                {"spoken_languages": {"$regex": searchQuery, "$options": "i"}}
            ]
        }

    # Fetch total number of matching movies
    total_movies = db.Movies.count_documents(query_filter)

    # Pagination logic
    movies_cursor = db.Movies.find(query_filter).skip((page - 1) * per_page).limit(per_page)
    movies = list(movies_cursor)

    # Add fields `in_cart` and `is_rented` to each movie based on the user's history
    # for movie in movies:
    #     movie['in_cart'] = db.orders.find_one({"movie_id": movie["_id"], "user_id": ObjectId(user_id)}) is not None
    #     movie['is_rented'] = db.history.find_one({"movie_id": movie["_id"], "user_id": ObjectId(user_id)}) is not None

    # Total pages calculation
    total_pages = (total_movies + per_page - 1) // per_page
    display_range = range(max(1, page - 14), min(total_pages + 1, page + 15))

    # Fetch top-rated movies for the carousel
    top_movies_cursor = db.Movies.aggregate([
        {"$lookup": {
            "from": "reviews",
            "localField": "_id",
            "foreignField": "movies_id",
            "as": "reviews"
        }},
        {"$addFields": {
            "avg_rating": {"$avg": "$reviews.rating"}
        }},
        {"$sort": {"avg_rating": -1}},
        {"$limit": 5}
    ])
    top_movies = list(top_movies_cursor)

    # Personalized recommendations based on user's most-watched genre
    # if user_id:
    #     # Find user's most-watched genre
    #     most_watched_genre = db.history.aggregate([
    #         {"$match": {"user_id": ObjectId(user_id)}},
    #         {"$lookup": {
    #             "from": "movies",
    #             "localField": "movie_id",
    #             "foreignField": "_id",
    #             "as": "movie"
    #         }},
    #         {"$unwind": "$movie"},
    #         {"$group": {
    #             "_id": "$movie.genre",
    #             "count": {"$sum": 1}
    #         }},
    #         {"$sort": {"count": DESCENDING}},
    #         {"$limit": 1}
    #     ])
    #     most_watched_genre = list(most_watched_genre)

    #     if most_watched_genre:
    #         genre = most_watched_genre[0]["_id"]
    #         recommendations_cursor = db.movies.aggregate([
    #             {"$match": {
    #                 "genre": genre,
    #                 "_id": {"$nin": [history["movie_id"] for history in db.history.find({"user_id": ObjectId(user_id)})]}
    #             }},
    #             {"$lookup": {
    #                 "from": "reviews",
    #                 "localField": "_id",
    #                 "foreignField": "movies_id",
    #                 "as": "reviews"
    #             }},
    #             {"$addFields": {
    #                 "avg_rating": {"$avg": "$reviews.rating"}
    #             }},
    #             {"$sort": {"avg_rating": DESCENDING}},
    #             {"$limit": 30}
    #         ])
    #         recommendations = list(recommendations_cursor)

    return render_template('index.html',
                           movies=movies,
                           page=page,
                           per_page=per_page,
                           searchName=searchQuery,
                           total_pages=total_pages,
                           display_range=display_range,
                           top_movies=top_movies, recommendations=recommendations)
