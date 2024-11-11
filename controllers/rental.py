from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
import config.constants
from datetime import datetime, timedelta
from bson import ObjectId

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

    db = current_app.mongo.db

    # Fetch rented movies for the user
    with current_app.app_context():
        # Retrieve purchase records for the user
        purchases = list(db.purchases.find({"users_id": ObjectId(user_id)}))
        
        # Retrieve movie rentals linked to the user's purchase history
        rented_movies = []
        for purchase in purchases:
            purchase_id = purchase["_id"]
            purchase_timestamp = purchase["purchase_timestamp"]

            # Retrieve history records for this purchase
            history_records = list(db.history.find({"purchase_id": ObjectId(purchase_id)}))

            for history in history_records:
                movie_id = ObjectId(history["movie_id"])
                movie = db.Movies.find_one({"_id": movie_id})

                if movie:
                    # Calculate the rental expiration date
                    rental_expiry = purchase_timestamp + timedelta(days=rental_period_days)
                    is_active = rental_expiry >= datetime.now()  # Check if rental is still active

                    # Append movie details along with the expiration date and rental status
                    rented_movies.append({
                        "id": movie["_id"],
                        "title": movie["title"],
                        "overview": movie["overview"],
                        "release_date": movie["release_date"],
                        "runtime": movie["runtime"],
                        "price": movie["price"],
                        "poster_path": movie["poster_path"],
                        "rental_expiry": rental_expiry,
                        "is_active": is_active
                    })

        # Pass the rented movies to the template
        return render_template('/rental/rental.html', movies=rented_movies)