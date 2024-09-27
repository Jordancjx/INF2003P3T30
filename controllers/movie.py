from flask import Blueprint, render_template, flash, request, redirect, current_app, url_for
import config.constants
from sqlalchemy import text
from config.dbConnect import db
from models.movie import Movie
from models.review import Review


movies_bp = Blueprint('movie', __name__, template_folder=config.constants.template_dir,
                      static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/movie')


@movies_bp.route('/single/<int:id>', methods=['GET'])
def single(id):
    with current_app.app_context():
        sql=text("SELECT * FROM movies WHERE id = :id")
        result=db.session.execute(sql, {"id": id})
        movie=result.fetchone()
        
        review_sql = text("SELECT * FROM reviews WHERE movies_id = :movies_id")
        result=db.session.execute(review_sql, {"movies_id": id})
        reviews=result.fetchall()

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))
        
        return render_template('movie/single.html', movie=movie, reviews=reviews)


# Api to update movies, won't render any page
@movies_bp.route("/api/update", methods=['POST'])
def post_update_movie():
    rq = request.form
    id = rq.get('movie_id')
    # langs = rq.getlist('langs[]')

    with current_app.app_context():
        sql=text("SELECT * FROM movies WHERE id = :id")
        result=db.session.execute(sql, {"id": id})
        movie=result.fetchone()

        if movie:
            sql=text("UPDATE movies SET name=:name, synopsis=:synopsis, price=:price, runtime=:runtime, release_date=:release_date")
            name = rq.get('moviename')
            synopsis = rq.get('synopsis')
            price = rq.get('price')
            runtime = rq.get('runtime')
            release_date = rq.get('release_date')
            # movie.trailer_link = rq.get("trailer_link")

            db.session.execute(sql, {"name":name, "synopsis":synopsis, "price":price, "runtime":runtime, "release_date":release_date})
            db.session.commit()

            return redirect(url_for('movie.single', id=id))
        else:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

   
@movies_bp.route('/update/<int:id>')
def update_movie(id):
    with current_app.app_context():
        sql=text("SELECT * FROM movies WHERE id = :id")
        result=db.session.execute(sql, {"id": id})
        movie=result.fetchone()

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

        return render_template('movie/update.html', movie=movie)

