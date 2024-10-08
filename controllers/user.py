from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
    old_password = request.form.get('old_password')

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
                stored_password_sql = text("SELECT password FROM users WHERE id = :user_id")
                stored_password_result = db.session.execute(stored_password_sql, {"user_id": user_id})
                stored_password = stored_password_result.scalar()

                if not check_password_hash(stored_password, old_password):
                    flash('Incorrect old password', 'error')
                    return redirect(url_for('user.getProfile'))

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
