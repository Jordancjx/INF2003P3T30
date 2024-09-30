from flask import Blueprint, render_template, flash, request, redirect, current_app, url_for
import config.constants
from sqlalchemy import text
from config.dbConnect import db
from models.movie import Movie
from werkzeug.utils import secure_filename
from models.review import Review
import os

movies_bp = Blueprint('movie', __name__, template_folder=config.constants.template_dir,
                      static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/movie')

UPLOAD_FOLDER = 'public/posters'  # Ensure this folder exists
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@movies_bp.route('/add')
def add():
    return render_template('movie/add.html')


@movies_bp.route('/search', methods=["POST"])
def search():
    search_name = request.form.get("searchName")
    return redirect(url_for('index.index', searchName=search_name))


@movies_bp.route('/single/<int:id>', methods=['GET'])
def single(id):
    with current_app.app_context():
        sql = text("SELECT * FROM movies LEFT JOIN reviews ON movies.id = reviews.movies_id LEFT JOIN users ON reviews.users_id = users.id WHERE movies.id = :id")
        result = db.session.execute(sql, {"id": id})
        rows = result.fetchall()

        if not rows:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))
        
        movie = rows[0]
        reviews = [row for row in rows if row.id]

        return render_template('movie/single.html', movie=movie, reviews=reviews)


# Api to add movies, won't render any page
@movies_bp.route('/api/add', methods=['POST'])
def post_add_movie():
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

            sql = text(
                "INSERT INTO movies (name, synopsis, release_date, runtime, price, image_url, trailer_link) "
                "VALUES (:name, :synopsis, :release_date, :runtime, :price, :image_url, :trailer_link)")
            result = db.session.execute(sql, {
                "name": request.form.get('moviename'),
                "synopsis": request.form.get("synopsis"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "price": request.form.get("price"),
                "image_url": poster_url,
                "trailer_link": request.form.get("trailer_link")
            })
            db.session.commit()
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
    # langs = rq.getlist('langs[]')

    with current_app.app_context():
        sql = text("SELECT * FROM movies WHERE id = :id")
        result = db.session.execute(sql, {"id": id})
        movie = result.fetchone()

        if movie:
            sql = text(
                "UPDATE movies "
                "SET name=:name, synopsis=:synopsis, price=:price, runtime=:runtime, release_date=:release_date")

            name = rq.get('moviename')
            synopsis = rq.get('synopsis')
            price = rq.get('price')
            runtime = rq.get('runtime')
            release_date = rq.get('release_date')
            # movie.trailer_link = rq.get("trailer_link")

            db.session.execute(sql, {"name": name, "synopsis": synopsis, "price": price, "runtime": runtime,
                                     "release_date": release_date})
            db.session.commit()

            return redirect(url_for('movie.single', id=id))
        else:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))


@movies_bp.route('/update/<int:id>')
def update_movie(id):
    with current_app.app_context():
        sql = text("SELECT * FROM movies WHERE id = :id")
        result = db.session.execute(sql, {"id": id})
        movie = result.fetchone()

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

        return render_template('movie/update.html', movie=movie)


@movies_bp.route('/api/delete/<int:id>', methods=['POST'])
def delete_movie(id):
    with current_app.app_context():
        sql = text("SELECT * FROM movies WHERE id = :id")
        result = db.session.execute(sql, {"id": id})
        movie = result.fetchone()

        if movie is None:
            flash('Movie not found', 'error')
            return redirect(url_for('index.index'))

        sql = text('DELETE from movies WHERE id = :id')
        db.session.execute(sql, {'id', id})
        db.session.commit()

        flash('Movie deleted successfully!', 'success')
        return redirect(url_for('index.index'))

#top-rated movie ratings
@movies_bp.route('/top-rated-movies')
def top_rated_movies():
    with current_app.app_context():
        sql = text("""SELECT m.name as movie.name, m.image_url as movie.image_url, COALESCE(AVG(r.rating,0) as avg_rating
                      FROM movies m
                      LEFT JOIN reviews r ON m.id = r.movies_id
                      GROUP BY m.id
                      ORDER BY avg_rating DESC;""")
        result = db.session.execute(sql)
        top_movies = result.fetchall()

        print(top_movies)

        return render_template('index.html', top_movies = top_movies)