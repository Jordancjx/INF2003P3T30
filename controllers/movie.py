from flask import Blueprint, render_template, flash, request, redirect, url_for
from sqlalchemy import text
import config.constants
from config.dbConnect import db
from models.movie import Movie


movies_bp = Blueprint('movie', __name__, template_folder=config.constants.template_dir,
                      static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/movie')


@movies_bp.route('/single/<int:id>', methods=['GET'])
def single(id):
    movie = Movie.query.get(id)

    if movie is None:
        flash('Movie not found', 'error')
        return redirect(url_for('index.index'))
    
    return render_template('movie/single.html', movie=movie)


# Api to update movies, won't render any page
@movies_bp.route("/api/update", methods=['POST'])
def post_update_movie():
    rq = request.form
    id = rq.get('movie_id')
    langs = rq.getlist('langs[]')

    movie = Movie.query.get(id)

    if movie:
        movie.name = rq.get('moviename')
        movie.synopsis = rq.get('synopsis')
        movie.price = rq.get('price')
        movie.runtime = rq.get('runtime')
        movie.release_date = rq.get('release_date')
        movie.trailer_link = rq.get("trailer_link")

        db.session.commit()

        return redirect(url_for(''))

    flash('Movie not found', 'error')
    return redirect(url_for('index.index'))


@movies_bp.route('/update/<int:id>')
def update_movie(id):
    movie = Movie.query.get(id)
    
    printed_langs = []
    if movie is None:
        flash('Movie not found', 'error')
        return redirect(url_for('index.index'))

    return render_template('movie/update.html', movie=movie)

