from flask import Blueprint, render_template, request, session
import config.constants
from config.dbConnect import get_db
from bson import ObjectId

index_bp = Blueprint('index', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/')


@index_bp.route('/')
async def index():
    recommendations = None
    searchQuery = request.args.get("searchName")
    page = request.args.get('page', default=1, type=int)  # Defaults to page 1 if not provided
    per_page = request.args.get('per_page', default=12, type=int)  # Defaults to 12 items per page if not provided

    db = await get_db()
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
    total_movies = await db.Movies.count_documents(query_filter)

    # Pagination logic
    movies_cursor = db.Movies.find(query_filter).skip((page - 1) * per_page).limit(per_page)
    movies = await movies_cursor.to_list(length=per_page)

    # Get a list of movie IDs that the user has in their orders (in the cart)
    order_movies = await db.orders.find({"users_id": ObjectId(user_id)}, {"movie_id": 1}).to_list(length=None)
    order_movie_ids = [
        ObjectId(order['movie_id']) for order in order_movies
    ]

    # Retrieve the list of purchase IDs for the user from the purchases collection
    purchases = await db.purchases.find({"users_id": ObjectId(user_id)}, {"_id": 1}).to_list(length=None)
    purchase_ids = [
        purchase['_id'] for purchase in purchases
    ]

    # Based on retrieved purchase IDs, find the movie IDs in the history collection
    rented_movies = await db.history.find({"purchase_id": {"$in": purchase_ids}}, {"movie_id": 1}).to_list(length=None)
    rented_movie_ids = [
        history['movie_id'] for history in rented_movies
    ]

    # Add `in_cart` and `is_rented` fields to each movie based on the above lists
    for movie in movies:
        movie['in_cart'] = movie["_id"] in order_movie_ids  # Check if the movie is in the cart
        movie['is_rented'] = movie["_id"] in rented_movie_ids  # Check if the movie is rented

    # Total pages calculation
    total_pages = (total_movies + per_page - 1) // per_page
    display_range = range(max(1, page - 14), min(total_pages + 1, page + 15))

    # Fetch top-rated movies for the carousel
    top_movies = await db.Movies.aggregate([
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
    ]).to_list(length=None)

    # Personalized recommendations based on user's most-watched genre
    if user_id:
        # Find user's most-watched genre
        most_watched_genre = await db.history.aggregate([
            {"$lookup": {
                "from": "purchases",
                "localField": "purchase_id",  # Match the purchase_id from history
                "foreignField": "_id",  # Match with _id in purchases
                "as": "purchase"
            }},

            {"$unwind": "$purchase"},
            {"$match": {"purchase.users_id": ObjectId(user_id)}},

            {"$lookup": {
                "from": "Movies",
                "localField": "movie_id",  # Match the movie_id from history
                "foreignField": "_id",  # Match with _id in Movies
                "as": "movie"
            }},

            {"$unwind": "$movie"},

            # Split the movie genres into an array
            {"$addFields": {
                "movie_genres": {
                    "$split": ["$movie.genres", ", "]
                }
            }},

            {"$unwind": "$movie_genres"},

            # Group by genre and their frequency
            {"$group": {
                "_id": "$movie_genres",  # Group by individual genre
                "count": {"$sum": 1}  # Count how many times each genre has been watched
            }},

            {"$sort": {"count": -1}},
            # Get the top 3 most watched genres for user
            {"$limit": 3}
        ]).to_list(length=None)

        if most_watched_genre:
            genres = [genre_entry["_id"] for genre_entry in most_watched_genre]  # Extract all genres

            # Fetch all movie IDs the user has watched to exclude from recommendations
            history = await db.history.find({"user_id": ObjectId(user_id)}).to_list(length=None)
            watched_movies = set(
                history["movie_id"] for hist in history
            )

            recommendations = await db.Movies.aggregate([
                {"$match": {
                    "_id": {"$nin": list(watched_movies)}  # Exclude movies the user has already watched
                }},
                {"$addFields": {
                    "genres_array": {"$split": ["$genres", ", "]},  # Split the genres string into an array
                }},
                {"$match": {
                    "genres_array": {"$in": genres}  # Match movies where any of the genres in the array match
                }},
                {"$lookup": {
                    "from": "reviews",
                    "localField": "_id",
                    "foreignField": "movies_id",
                    "as": "reviews"
                }},
                {"$addFields": {
                    "avg_rating": {"$ifNull": [{"$avg": "$reviews.rating"}, 0]}  # Default to 0 if no reviews
                }},
                {"$sort": {"avg_rating": -1}},  # Sort by average rating (highest first)
                {"$limit": 30}  # Limit to top 30 recommendations
            ]).to_list(length=None)

    return render_template('index.html',
                           movies=movies,
                           page=page,
                           per_page=per_page,
                           searchName=searchQuery,
                           total_pages=total_pages,
                           display_range=display_range,
                           top_movies=top_movies, recommendations=recommendations)