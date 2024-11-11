from flask import Blueprint, render_template, flash, request, redirect, current_app, url_for, session
import config.constants
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from bson import ObjectId

movies_bp = Blueprint('movie', __name__, template_folder=config.constants.template_dir,
                      static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/movie')

UPLOAD_FOLDER = 'public/posters'  # Ensure this folder exists
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@movies_bp.route('/add')
def add():
    # check if user is logged in and is admin
    if 'user_id' not in session or 'admin' not in session:
        flash('You must be logged in as an admin to add a movie.', 'error')
        return redirect(url_for('index.index'))

    # if user is logged in, render the add movie page
    return render_template('movie/add.html')


@movies_bp.route('/search', methods=["POST"])
def search():
    search_name = request.form.get("searchName")
    return redirect(url_for('index.index', searchName=search_name))


@movies_bp.route('/single/<string:id>', methods=['GET'])
def single(id):
    rental_period_days = 7  # Rental period of 7 days
    rental_expiry = None
    is_active = None
    review_exists = False
    db = current_app.mongo.db

    with current_app.app_context():
        if 'user_id' in session:
            user_id = session['user_id']
            movie = db.Movies.find_one({"_id": ObjectId(id)}), {"name": 1, "genres": 1, "language": 1, "description": 1}

            if not movie:
                flash('Movie not found', 'error')
                return redirect(url_for('index.index'))

            # Fetch all reviews for the movie
            # reviews = list(db.reviews.find({"movies_id": ObjectId(id)}).sort("timestamp", -1))

            reviews = db.reviews.aggregate([
                {
                    "$match": {"movies_id": ObjectId(id)}
                },
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "users_id",
                        "foreignField": "_id",
                        "as": "user_info"
                    }
                },
                {
                    "$unwind": "$user_info"
                },
                {
                    "$project": {
                        "rating": 1,
                        "body": 1,
                        "movies_id": 1,
                        "user_info.username": 1,
                        "user_info._id": {"$toString": "$user_info._id"},
                    }
                }
            ])

            user_id = str(session.get('user_id')) if 'user_id' in session else None

            reviews = list(reviews)
            for review in reviews:
                review['user_info']['_id'] = str(review['user_info']['_id'])
                if review['user_info']['_id'] == user_id:
                    review['user_info']['user'] = 1
                else:
                    review['user_info']['user'] = 0

            review_check = db.reviews.count_documents({"users_id": user_id, "movies_id": ObjectId(id)})
            review_exists = review_check > 0

        else:
            movie = db.Movies.find_one({"_id": ObjectId(id)}), {"name": 1, "genres": 1, "language": 1, "description": 1}
            if not movie:
                flash('Movie not found', 'error')
                return redirect(url_for('index.index'))

            reviews = list(db.Reviews.find({"movies_id": ObjectId(id)}).sort("timestamp", -1))

        return render_template('movie/single.html', movie=movie[0], review_exists=review_exists, reviews=reviews,
                               user_id=user_id)


# Api to add movies, won't render any page
@movies_bp.route('/api/add', methods=['POST'])
def post_add_movie():
    # check if user is logged in and is admin
    if 'user_id' not in session or 'admin' not in session:
        flash('You must be logged in as an admin to add a movie.', 'error')
        return redirect(url_for('index.index'))

    db = current_app.mongo.db

    with current_app.app_context():
        try:
            poster_url = None
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file.filename != '':
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        poster_url = f"/{file_path}"

            movie_document = {
                "title": request.form.get('moviename'),
                "overview": request.form.get("synopsis"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "price": request.form.get("price"),
                "image_url": poster_url,
                "trailer_link": request.form.get("trailer_link")
            }

            db.Movies.insert_one(movie_document)

            flash('Movie has been added.', 'success')
            return redirect(url_for('movie.add'))
        except Exception as e:
            print(e)
            flash('An error has occurred.', 'error')
            return redirect(url_for('movie.add'))


# Api to update movies, won't render any page
@movies_bp.route("/api/update", methods=['POST'])
def post_update_movie():
    rq = request.form
    id = rq.get('movie_id')

    db = current_app.mongo.db

    with current_app.app_context():
        movie = db.Movies.find_one({"_id": ObjectId(id)})

        if movie:
            updated_fields = {
                "name": rq.get('moviename'),
                "synopsis": rq.get('synopsis'),
                "price": rq.get('price'),
                "runtime": rq.get('runtime'),
                "release_date": rq.get('release_date')
            }

            db.Movies.update_one(
                {"_id": ObjectId(id)},
                {"$set": updated_fields}
            )

            return redirect(url_for('movie.single', id=id))
        else:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))


@movies_bp.route('/update/<string:id>')
def update_movie(id):
    db = current_app.mongo.db

    with current_app.app_context():
        movie = db.Movies.find_one({"_id": ObjectId(id)})

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

        return render_template('movie/update.html', movie=movie)


@movies_bp.route('/api/delete/<string:id>', methods=['POST'])
def delete_movie(id):
    db = current_app.mongo.db

    with current_app.app_context():
        movie = db.Movies.find_one({"_id": ObjectId(id)})

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

        result = db.Movies.delete_one({"_id": ObjectId(id)})

        if result.deleted_count > 0:
            flash('Movie deleted successfully!', 'success')
            return redirect(url_for('index.index'))

        else:
            flash('Error while deleting movie', 'error')
            return redirect(url_for('index.index'))
