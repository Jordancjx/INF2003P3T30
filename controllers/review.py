from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.review import Review

reviews_bp = Blueprint('review', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/review')


@reviews_bp.route('/api/add', methods=['POST'])
def add():
    body=request.form.get('review')
    rating=int(request.form.get('rating'))
    movies_id=request.form.get('movie_id')
    users_id=session.get('user_id')

    with current_app.app_context():
        try:
            insertsql = text("INSERT INTO reviews (body, rating, movies_id, users_id) VALUES (:body, :rating, :movies_id, :users_id)")
            db.session.execute(insertsql, {"body":body, "rating":rating, "movies_id":movies_id, "users_id":users_id})
            db.session.commit()
            flash('Review posted successfully!')
            return redirect(url_for('movie.single', id=movies_id))

        except Exception as e:
            db.session.rollback()
            flash("An error has occurred", "error")
            return redirect(url_for('movie.single', id=movies_id))


@reviews_bp.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    with current_app.app_context():
        sql=text("SELECT * FROM reviews WHERE id = :id")
        result=db.session.execute(sql, {"id": id})
        review=result.fetchone()
        
        if review is None:
            flash('Review not found', 'error')
            return redirect(url_for('index.index'))

        return render_template('review/edit.html', review=review)
