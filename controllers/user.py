from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

UPLOAD_FOLDER = 'public/profile_pics'  # Ensure this folder exists
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

user_bp = Blueprint('user', __name__, template_folder=config.constants.template_dir,
                    static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/user')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Register
@user_bp.route('/register')
def register():
    return render_template('/user/register.html')


# Login
@user_bp.route('/login')
def login():
    return render_template('/user/login.html')


# Logout
@user_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index.index'))


# Profile
@user_bp.route('/profile')
def getProfile():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for('user.login'))

    with current_app.app_context():
        sql = text("SELECT * FROM users WHERE id = :id")
        result = db.session.execute(sql, {"id": session['user_id']})
        user = result.fetchone()

        if user is None:
            flash("User not found.", "error")
            return redirect(url_for('user.login'))

    return render_template('/user/profile.html', user=user)


# cart
@user_bp.route('/cart')
def cart():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    with current_app.app_context():
        # Fetch the user's orders and join with the movies table to get movie names
        sql = text("""
            SELECT orders.id, orders.order_timestamp, orders.total_price, movies.name 
            FROM orders 
            JOIN movies ON orders.movie_id = movies.id 
            WHERE orders.users_id = :user_id
        """)
        result = db.session.execute(sql, {"user_id": user_id})
        orders = result.fetchall()

        # Calculate the total sum of prices
        total_sum_sql = text("SELECT COALESCE(SUM(total_price), 0) as total_sum FROM orders WHERE users_id = :user_id")
        total_sum_result = db.session.execute(total_sum_sql, {"user_id": user_id})
        total_sum = total_sum_result.fetchone().total_sum

        # Pass the fetched data to the cart template
        return render_template('/user/cart.html', orders=orders, total_sum=total_sum)


# Register API; Does not render any page
@user_bp.route('/api/register', methods=["POST"])
def register_process():
    hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=16)
    username = request.form.get('username')
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')

    if not all([username, fname, lname, email, hashed_password]):
        flash("Not all fields are filled", "error")
        return redirect(url_for('user.register'))

    with current_app.app_context():
        sql = text("SELECT * FROM users WHERE username = :username OR email = :email")
        result = db.session.execute(sql, {"username": username, "email": email})
        existing_user = result.fetchone()

        if existing_user:
            flash("Username or Email already exists", "error")
            return redirect(url_for('user.register'))

        insert = text(
            "INSERT INTO users (username, fname, lname, email, password, email_validated, admin_controls) "
            "VALUES (:username, :fname, :lname, :email, :password, :email_validated, :admin_controls)")

        try:
            db.session.execute(insert, {"username": username, "fname": fname, "lname": lname, "email": email,
                                        "password": hashed_password, "email_validated": False, "admin_controls": False})
            db.session.commit()
            flash('Registered successfully!', 'success')
            return redirect(url_for('user.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error has occurred during registration.', "error")
            return redirect(url_for('user.register'))


# Login API; Does not render any page
@user_bp.route('/api/login', methods=["POST"])
def login_process():
    identifier = request.form.get('username')  # This could be either email or username
    password = request.form.get('password')

    with current_app.app_context():
        sql = text("SELECT * FROM users WHERE username = :identifier OR email = :identifier LIMIT 1")
        result = db.session.execute(sql, {"identifier": identifier})
        user = result.fetchone()

    if user and check_password_hash(user.password, password):
        if user.admin_controls:
            session['admin'] = True
        session['user_id'] = user.id

        flash('Logged in successfully!', 'success')
        return redirect(url_for('index.index'))

    else:
        flash("Invalid Username/email or Password", "error")
        return redirect(url_for('user.login'))


@user_bp.route('/api/update_profile', methods=["POST"])
def update_profile():
    if 'user_id' not in session:
        flash("Please log in to update your profile.", "error")
        return redirect(url_for('user.login'))

    user_id = session["user_id"]
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    password = request.form.get('password')

    profile_pic_url = None
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file.filename != '':
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                profile_pic_url = f"/{file_path}"

    with current_app.app_context():
        try:
            params = {
                "fname": fname,
                "lname": lname,
                "email": email,
                "user_id": user_id
            }

            updatesql = "UPDATE users SET fname = :fname, lname = :lname, email = :email"

            if profile_pic_url:
                updatesql += ", profile_pic_url = :profile_pic_url"
                params["profile_pic_url"] = profile_pic_url

            if password:
                hashed_password = generate_password_hash(password)
                updatesql += ", password = :password"
                params["password"] = hashed_password

            updatesql += " WHERE id = :user_id"

            db.session.execute(text(updatesql), params)
            db.session.commit()

            flash("Profile updated successfully!", "success")
            return redirect(url_for('user.getProfile'))

        except Exception as e:
            db.session.rollback()
            print(e)
            flash("An error occurred while updating the profile", "error")
            return redirect(url_for('user.getProfile'))


# User's Rented Movies Page
@user_bp.route('/movies')
def rented_movies():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your rented movies.", "error")
        return redirect(url_for('user.login'))
    
    user_id = session['user_id']
    rental_period_days = 7  # Rental period of 7 days
    with current_app.app_context():
        # Fetch rented movies
        sql = text("""
            SELECT m.id, m.name, m.synopsis, m.release_date, m.runtime, m.price, m.image_url, p.purchase_timestamp
            FROM movies m
            INNER JOIN history h ON h.movie_id = m.id
            INNER JOIN purchases p ON h.purchase_id = p.id
            WHERE p.users_id = :user_id
        """)
        result = db.session.execute(sql, {"user_id": user_id})
        movies = result.fetchall()

        # Calculate expiration dates and check if rentals are still active
        rented_movies = []
        for movie in movies:
            purchased_at = movie.purchase_timestamp  # Rental start date
            rental_expiry = datetime.strptime(purchased_at, "%Y-%m-%d %H:%M:%S.%f") + timedelta(days=rental_period_days)  # Expiration date
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
        
        # Pass the rented movies to the template
        return render_template('/user/movies.html', movies=rented_movies)


# Rented Movie Details Page
@user_bp.route('/movies_detail/<int:movie_id>')
def movie_details(movie_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view movie details.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    rental_period_days = 7  # Rental period of 7 days
    
    with current_app.app_context():
        # Fetch movie details
        movie_sql = text("""
            SELECT m.*, r.body AS review_body, r.rating AS review_rating, r.id AS review_id, p.purchase_timestamp AS rental_date 
            FROM movies m
            LEFT JOIN reviews r ON r.movies_id = m.id AND r.users_id = :user_id
			INNER JOIN purchases p ON p.users_id = :user_id
			INNER JOIN history h ON h.purchase_id = p.id AND h.movie_id = m.id
            WHERE m.id = :movie_id
        """)
        movie_result = db.session.execute(movie_sql, {"user_id": user_id, "movie_id": movie_id})
        movie = movie_result.fetchone()

        # Calculate expiration date
        rental_expiry = None
        if movie.rental_date:
            rental_expiry = datetime.strptime(movie.rental_date, "%Y-%m-%d %H:%M:%S.%f") + timedelta(days=rental_period_days)
        
        # Fetch all reviews for the movie
        reviews_sql = text("""
            SELECT r.*, u.username 
            FROM reviews r
            JOIN users u ON r.users_id = u.id
            WHERE r.movies_id = :movie_id
        """)
        reviews_result = db.session.execute(reviews_sql, {"movie_id": movie_id})
        reviews = reviews_result.fetchall()

    return render_template('/user/movies_detail.html', datetime=datetime, movie=movie, reviews=reviews, rental_expiry=rental_expiry)


# Edit Review in Rented Movie Details Page
@user_bp.route('/api/edit/<int:review_id>', methods=['POST'])
def edit_review(review_id):
    if 'user_id' not in session:
        flash("Please log in to edit your review.", "error")
        return redirect(url_for('user.login'))

    # Get form data
    movie_id = request.form.get('movie_id')
    rating = request.form.get('rating')
    review_body = request.form.get('review')
    user_id = session['user_id']

    if not rating or not review_body:
        flash("Please fill out all fields.", "error")
        return redirect(url_for('user.movie_details', movie_id=movie_id))

    # Ensure the user owns the review before editing
    try:
        review_sql = text("""
            SELECT * FROM reviews WHERE id = :review_id AND users_id = :user_id
        """)
        review_result = db.session.execute(review_sql, {"review_id": review_id, "user_id": user_id})
        review = review_result.fetchone()

        if not review:
            flash("You do not have permission to edit this review.", "error")
            return redirect(url_for('user.movie_details', movie_id=movie_id))

        # Update the review
        update_sql = text("""
            UPDATE reviews
            SET rating = :rating, body = :review_body, written_date = CURRENT_TIMESTAMP
            WHERE id = :review_id
        """)
        db.session.execute(update_sql, {
            "rating": rating,
            "review_body": review_body,
            "review_id": review_id
        })
        db.session.commit()

        flash("Review updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error editing review. Please try again.", "error")
    
    return redirect(url_for('user.movie_details', movie_id=movie_id))


# Add Review in Rented Movie Details Page
@user_bp.route('/api/add_review', methods=['POST'])
def add_review():
    if 'user_id' not in session:
        flash("Please log in to add a review.", "error")
        return redirect(url_for('user.login'))

    # Get form data
    movie_id = request.form.get('movie_id')
    rating = request.form.get('rating')
    review_body = request.form.get('review')
    user_id = session['user_id']
    
    if not movie_id or not rating or not review_body:
        flash("Please fill out all fields.", "error")
        return redirect(url_for('user.movie_details', movie_id=movie_id))

    # Insert the review into the database
    try:
        insert_sql = text("""
            INSERT INTO reviews (movies_id, users_id, rating, body, written_date)
            VALUES (:movie_id, :user_id, :rating, :review_body, CURRENT_TIMESTAMP)
        """)
        db.session.execute(insert_sql, {
            "movie_id": movie_id,
            "user_id": user_id,
            "rating": rating,
            "review_body": review_body
        })
        db.session.commit()

        flash("Review added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error adding review. Please try again.", "error")
    
    return redirect(url_for('user.movie_details', movie_id=movie_id))