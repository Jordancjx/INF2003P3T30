from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
from sqlalchemy import text
import config.constants
from datetime import datetime, timedelta
from config.dbConnect import db

rentals_bp = Blueprint('rental', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/rentals')


# User's Rented Movies Page
@rentals_bp.route('/')
def rentals():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your rented movies.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    rental_period_days = 7  # Rental period of 7 days

    with current_app.app_context():
        # Fetch rented movies
        rented_movies_sql = text("""
            SELECT m.id, m.name, m.synopsis, m.release_date, m.runtime, m.price, m.image_url, p.purchase_timestamp
            FROM movies m
            INNER JOIN history h ON h.movie_id = m.id
            INNER JOIN purchases p ON h.purchase_id = p.id
            WHERE p.users_id = :user_id
        """)
        result = db.session.execute(rented_movies_sql, {"user_id": user_id})
        movies = result.fetchall()

        # Calculate expiration dates and check if rentals are still active
        rented_movies = []
        for movie in movies:
            purchased_at = movie.purchase_timestamp  # Rental start date
            rental_expiry = datetime.strptime(purchased_at, "%Y-%m-%d %H:%M:%S.%f") + timedelta(
                days=rental_period_days)  # Expiration date
            is_active = rental_expiry >= datetime.now()  # Check if rental is still active

            # Append movie details along with the expiration date and rental status
            rented_movies.append({
                "id": movie.id,
                "name": movie.name,
                "synopsis": movie.synopsis,
                "release_date": movie.release_date,
                "runtime": movie.runtime,
                "price": movie.price,
                "image_url": movie.image_url,
                "rental_expiry": rental_expiry,
                "is_active": is_active
            })

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
            SELECT m.id, m.name, m.synopsis, m.release_date, m.runtime, m.price, m.image_url
            FROM movies m
            WHERE m.image_url IS NOT NULL AND m.genre IN (
                SELECT genre FROM most_watched_genre
            )
            AND m.id NOT IN (
                SELECT h.movie_id
                FROM history h
                INNER JOIN purchases p ON h.purchase_id = p.id
                WHERE p.users_id = :user_id
            )
            LIMIT 30;
        """)
        result = db.session.execute(recommendation_sql, {"user_id": user_id})
        recommendations = result.fetchall()

        # Pass the rented movies to the template
        return render_template('/rental/rental.html', movies=rented_movies, recommendations=recommendations)
