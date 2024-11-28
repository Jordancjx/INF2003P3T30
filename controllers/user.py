from bson import ObjectId
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
import config.constants
from config.dbConnect import get_db, get_client_and_db
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
async def getProfile():
    db = await get_db()

    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for('user.login'))

    user = await db.users.find_one({"_id": ObjectId(session['user_id'])})

    if user is None:
        flash("User not found.", "error")
        return redirect(url_for('user.login'))

    return render_template('/user/profile.html', user=user)


# cart
@user_bp.route('/cart')
async def cart():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    db = await get_db()

    # Fetch the user's orders and join with the movies table to get movie names
    orders = await db.orders.aggregate([
        {"$match": {"users_id": ObjectId(user_id)}},
        {"$lookup": {
            "from": "Movies",
            "localField": "movie_id",
            "foreignField": "_id",
            "as": "movie_details"
        }},
        {"$unwind": "$movie_details"},
        {"$addFields": {"movie_name": "$movie_details.title"}},
        {"$project": {
            "movie_name": 1,
            "total_price": 1,
            "order_timestamp": 1
        }}
    ]).to_list(length=None)

    total_sum = sum(order.get("total_price", 0) for order in orders)

    # Pass the fetched data to the cart template
    return render_template('/user/cart.html', orders=orders, total_sum=total_sum)


# Register API; Does not render any page
@user_bp.route('/api/register', methods=["POST"])
async def register_process():
    hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=16)
    username = request.form.get('username')
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')

    if not all([username, fname, lname, email, hashed_password]):
        flash("Information missing", "error")
        return redirect(url_for('user.register'))

    client, db = await get_client_and_db()
    existing_user = await db.users.find_one({"$or": [{"username": username}, {"email": email}]})

    if existing_user:
        flash("Username or Email already exists", "error")
        return redirect(url_for('user.register'))

    user_data = {
        "username": username,
        "fname": fname,
        "lname": lname,
        "email": email,
        "password": hashed_password,
        "email_validated": False,
        "admin_controls": False
    }

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.users.insert_one(user_data, session=client_session)
                flash('Registered successfully!', 'success')
                return redirect(url_for('user.login'))

            except Exception as e:
                flash('An error has occurred during registration.', "error")
                return redirect(url_for('user.register'))


# Login API; Does not render any page
@user_bp.route('/api/login', methods=["POST"])
async def login_process():
    identifier = request.form.get('username')  # This could be either email or username
    password = request.form.get('password')

    db = await get_db()
    user = await db.users.find_one({"$or": [{"username": identifier}, {"email": identifier}]})

    if user and check_password_hash(user['password'], password):
        if user.get('admin_controls', False):
            session['admin'] = True
        session['user_id'] = str(user['_id'])

        flash('Logged in successfully!', 'success')
        return redirect(url_for('index.index'))

    else:
        flash("Invalid Username/email or Password", "error")
        return redirect(url_for('user.login'))


@user_bp.route('/api/update_profile', methods=["POST"])
async def update_profile():
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

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                update_data = {
                    "fname": fname,
                    "lname": lname,
                    "email": email,
                }

                if profile_pic_url:
                    update_data["profile_pic_url"] = profile_pic_url

                if password:
                    user = await db.users.find_one({"_id": ObjectId(user_id)})
                    stored_password = user.get("password")

                    if not check_password_hash(stored_password, old_password):
                        flash('Incorrect old password', 'error')
                        return redirect(url_for('user.getProfile'))

                    hashed_password = generate_password_hash(password)
                    update_data["password"] = hashed_password

                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}, session=client_session
                )

                flash("Profile updated successfully!", "success")
                return redirect(url_for('user.getProfile'))

            except Exception as e:
                print(e)
                flash("An error occurred while updating the profile", "error")
                return redirect(url_for('user.getProfile'))
