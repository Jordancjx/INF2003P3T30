from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.review import Review

reviews_bp = Blueprint('review', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/review')


@reviews_bp.route('/api/add', methods=['POST'])
def add():
    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movies_id = request.form.get('movie_id')
    users_id = session.get('user_id')

    with current_app.app_context():
        try:
            insertsql = text(
                "INSERT INTO reviews (body, rating, movies_id, users_id) "
                "VALUES (:body, :rating, :movies_id, :users_id)")
            db.session.execute(insertsql,
                               {"body": body, "rating": rating, "movies_id": movies_id, "users_id": users_id})

            db.session.commit()
            flash('Review posted successfully!')
            return redirect(url_for('movie.single', id=movies_id))

        except Exception as e:
            db.session.rollback()
            flash("An error has occurred", "error")
            return redirect(url_for('movie.single', id=movies_id))


@reviews_bp.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    users_id = session.get('user_id')  # Get the current user ID

    with current_app.app_context():
        sql = text("SELECT * FROM reviews WHERE id = :id AND users_id = :users_id")
        result = db.session.execute(sql, {"id": id, "users_id": users_id})
        review = result.fetchone()

        if review is not None:
            flash('Review not found or you do not have the permission to edit', 'error')
            return redirect(url_for('index.index'))

        return render_template('review/edit.html', review=review)


@reviews_bp.route('/edit/<int:id>', methods=['POST'])
def update(id):
    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movie_id = request.form.get('movie_id')
    users_id = session.get('user_id')  # Get the current user ID

    with current_app.app_context():
        try:
            review_sql = text("""
                        SELECT * FROM reviews WHERE id = :review_id AND users_id = :user_id
                    """)
            review_result = db.session.execute(review_sql, {"review_id": id, "user_id": users_id})
            review = review_result.fetchone()

            if review is not None:
                flash("You do not have permission to edit this review.", "error")
                return redirect(url_for('movie.single', id=movie_id))

            sql = text("UPDATE reviews SET body = :body, rating = :rating WHERE id = :id AND users_id = :users_id")
            db.session.execute(sql, {"body": body, "rating": rating, "id": id, "users_id": users_id})
            db.session.commit()

            flash('Review updated successfully!')
            return redirect(url_for('movie.single', id=movie_id))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the review", "error")
            return redirect(url_for('movie.single', id=movie_id))


@reviews_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    users_id = session.get('user_id')  # Get the current user ID

    with current_app.app_context():
        try:
            review_sql = text("""
                                    SELECT * FROM reviews WHERE id = :review_id AND users_id = :user_id
                                """)
            review_result = db.session.execute(review_sql, {"review_id": id, "user_id": users_id})
            review = review_result.fetchone()

            if review:
                flash("You do not have permission to edit this review.", "error")
                return redirect(url_for('movie.single', id=id))

            sql = text("DELETE FROM reviews WHERE id = :id AND users_id = :users_id")
            db.session.execute(sql, {"id": id, "users_id": users_id})
            db.session.commit()

            flash('Review deleted successfully!')
            return redirect(url_for('movie.single', id=request.form.get('movie_id')))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the review", "error")
            return redirect(url_for('movie.single', id=request.form.get('movie_id')))
