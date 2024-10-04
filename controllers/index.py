from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
import config.constants
from sqlalchemy import text
from models.movie import Movie
from config.dbConnect import db

index_bp = Blueprint('index', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/')


@index_bp.route('/')
def index():
    searchName = request.args.get("searchName")
    page = request.args.get('page', default=1, type=int)  # Defaults to page 1 if not provided
    per_page = request.args.get('per_page', default=12, type=int)  # Defaults to 10 items per page if not provided
    
    with current_app.app_context():
        if searchName:
            total_sql = text("SELECT COUNT(*) FROM movies WHERE name LIKE :name")
            total_result = db.session.execute(total_sql, {"name": f"%{searchName}%"})
            total_movies = total_result.scalar()  # Get the total number of movies
            
            sql = text("""
                SELECT * FROM movies 
                WHERE name LIKE :name
                LIMIT :limit OFFSET :offset
            """)
            result = db.session.execute(sql, {
                "name": f"%{searchName}%",
                "limit": per_page,
                "offset": (page - 1) * per_page
            })
        else:
            # Count total movies (for pagination)
            total_sql = text("SELECT COUNT(*) FROM movies")
            total_result = db.session.execute(total_sql)
            total_movies = total_result.scalar()  # Get the total number of movies
            sql = text("""
                SELECT * FROM movies 
                LIMIT :limit OFFSET :offset
            """)
            result = db.session.execute(sql, {
                "limit": per_page,
                "offset": (page - 1) * per_page  # Calculate the offset based on page number
            })
            
        movies = result.fetchall()
        
        total_pages = (total_movies + per_page - 1) // per_page  # Total pages logic
        display_range = range(max(1, page - 14), min(total_pages + 1, page + 15))

    # Fetch top-rated movies for the carousel
    with current_app.app_context():
        top_rated_sql = text("""
            SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM movies m
            LEFT JOIN reviews r ON m.id = r.movies_id
            GROUP BY m.id
            ORDER BY avg_rating DESC
            LIMIT 5;
        """)
        top_rated_result = db.session.execute(top_rated_sql)
        top_movies = top_rated_result.fetchall()

    if 'user_id' in session:
        user_id = session['user_id']
        with current_app.app_context():
            # Fetch user's most watched genre and recommend unwatched movies from user's most watched genre
            recommendation_sql = text("""
                WITH most_watched_genre AS (
                    SELECT m.genre, COUNT(m.id) AS genre_count
                    FROM movies m
                    INNER JOIN history h ON h.movie_id = m.id
                    INNER JOIN purchases p ON h.purchase_id = p.id
                    WHERE p.users_id = :user_id
                    GROUP BY m.genre
                    ORDER BY genre_count DESC
                    LIMIT 1
                )
                SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating
                FROM movies m
                LEFT JOIN reviews r ON m.id = r.movies_id
                WHERE m.image_url IS NOT NULL AND m.genre IN (
                    SELECT genre FROM most_watched_genre
                )
                AND m.id NOT IN (
                    SELECT h.movie_id
                    FROM history h
                    INNER JOIN purchases p ON h.purchase_id = p.id
                    WHERE p.users_id = :user_id
                )
                GROUP BY m.id
                LIMIT 30;
            """)
            result = db.session.execute(recommendation_sql, {"user_id": user_id})
            recommendations = result.fetchall()

    return render_template('index.html', 
                           movies=movies, 
                           page=page, 
                           per_page=per_page, 
                           total_pages=total_pages,
                           display_range=display_range,
                           top_movies=top_movies, recommendations=recommendations)
