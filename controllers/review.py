from flask import Blueprint, render_template, flash, request, redirect, url_for, session
import config.constants
from config.dbConnect import db
from models.review import Review

reviews_bp = Blueprint('review', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/review')


@reviews_bp.route('/api/add', methods=['POST'])
def add():
    new_review = Review(
        body=request.form.get('review'),
        rating=request.form.get('rating'),
        movies_id=request.form.get('movie_id'),
        users_id=session.get('user_id')
    )

    try:
        db.session.add(new_review)
        db.session.commit()
        flash('Review posted successfully!')
        return redirect(url_for('movie.single', id=id))

    except Exception as e:
        db.session_rollback()
        flash("An error has occurred", "error")
        return redirect(url_for('movie.single', id=id))


@reviews_bp.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    review = Review.query.get(id)
    if review is None:
        flash('Review not found', 'error')
        return redirect(url_for('index.index'))

    return render_template('review/edit.html', review=review)
