from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.review import Review
from controllers.user import user_bp
from controllers.movie import movies_bp
from bson import ObjectId

reviews_bp = Blueprint('review', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/review')


@reviews_bp.route('/api/add', methods=['POST'])
def add():
    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movies_id = request.form.get('movie_id')
    users_id = session.get('user_id')
    print(movies_id)
    db = current_app.mongo.db
    
    review = {
        "body": body,
        "rating": rating,
        "movies_id" : ObjectId(request.form.get('movie_id')),
        "users_id": ObjectId(session.get('user_id'))
    }
    
    if not users_id:
        flash("Please log in to post a review", "error")
        return redirect(url_for(user_bp.login))
    
    with current_app.app_context():
        try:
            db.reviews.insert_one(review)
            flash('Review posted successfully!')
            return redirect(url_for('movie.single', id=movies_id))

        except Exception as e:
            flash("An error has occurred", "error")
            return redirect(url_for('movie.single', id=movies_id))


@reviews_bp.route('/edit/<string:id>', methods=['GET'])
def edit(id):
    users_id = session.get('user_id')  # Get the current user ID
    print(id)
    with current_app.app_context():
        db = current_app.mongo.db
        review = db.reviews.find_one(
            {"_id": ObjectId(id), "users_id": ObjectId(users_id)},  # Filter by both _id and user_id
            {"body": 1, "rating": 1, "movies_id": 1, "users_id": 1}  # Fields to return
        )
        print(review)
        if review is None:
            flash('Review not found or you do not have the permission to edit', 'error')
            return redirect(url_for('index.index'))

        return render_template('review/edit.html', review=review)


@reviews_bp.route('/api/update', methods=['POST'])
def update():
    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movie_id = ObjectId(request.form.get('movie_id'))
    users_id = ObjectId(session.get('user_id'))  # Get the current user ID
    review_id = ObjectId(request.form.get('review_id'))
    with current_app.app_context():
        try:
            db = current_app.mongo.db
            
            review = db.reviews.find_one({"_id": review_id, "users_id": users_id})

            if review is None:
                flash("You do not have permission to edit this review.", "error")
                return redirect(url_for('movie.single', id=movie_id))

            db.reviews.update_one(
                {"_id": review_id},  # Find the review by ID
                {"$set": {"body": body, "rating": rating}}  # Set new body and rating
            )

            flash('Review updated successfully!')
            return redirect(url_for('movie.single', id=movie_id))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the review", "error")
            return redirect(url_for('movie.single', id=movie_id))


@reviews_bp.route('/api/delete/<string:id>', methods=['POST'])
def delete(id):
    users_id = ObjectId(session.get('user_id'))  # Get the current user ID
    review_id = ObjectId(id)
    movie_id = request.form.get('movie_id')
    
    with current_app.app_context():
        try:
            db = current_app.mongo.db
            
            review = db.reviews.find_one({"_id": review_id, "users_id": users_id})
            if not review:
                flash("You do not have permission to edit this review.", "error")
                return redirect(url_for('movie.single', id=movie_id))

            db.reviews.delete_one({"_id": review_id, "users_id": users_id})

            flash('Review deleted successfully!')
            return redirect(url_for('movie.single', id=movie_id))

        except Exception as e:
            flash("An error occurred while updating the review", "error")
            return redirect(url_for('movie.single', id=movie_id))
