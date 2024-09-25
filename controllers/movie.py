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

    # sql = text('''
    #         SELECT
    #             m.*,
    #             GROUP_CONCAT(DISTINCT l.name) AS languages,
    #             GROUP_CONCAT(DISTINCT g.name) AS genres,
    #             AVG(r.rating) AS average_rating,
    #             COUNT(DISTINCT r.id) AS total_reviews,
    #             (SELECT JSON_ARRAYAGG(JSON_OBJECT('rating', r2.rating, 'user_id', r2.users_id, 'body', r2.body))
    #             FROM reviews r2
    #             WHERE r2.movies_id = m.id) AS reviews
    #         FROM
    #             movies m
    #         LEFT JOIN
    #             movies_has_languages ml ON m.id = ml.movies_id
    #         LEFT JOIN
    #             languages l ON ml.languages_id = l.id
    #         LEFT JOIN
    #             movies_has_genres mg ON m.id = mg.movies_id
    #         LEFT JOIN
    #             genres g ON mg.genres_id = g.id
    #         LEFT JOIN
    #             reviews r ON m.id = r.movies_id
    #         WHERE m.id = :id
    #     ''')
    #
    # result = db.session.execute(sql, {"id": id})
    # movie = result.fetchone()
    # if movie.reviews:
    #     reviews = json.loads(movie.reviews)
    # else:
    #     reviews = []
    return render_template('movie/single.html', movie=movie)


# Api to delete movies, won't render any page
# @movies_bp.route("/api/delete/<int:id>", methods=['DELETE'])
# def deleteMovie(id):
#     sql = text("DELETE FROM movies WHERE id = :id")
#     result = db.session.execute(sql, {"id": id})
#
#     # Commit the transaction
#     db.session.commit()
#
#     # If Movie is not found
#     if result.rowcount == 0:
#         return jsonify({'error': 'Movie not found'}), 404
#
#     return jsonify({'message': result.rowcount}), 200


# Api to update movies, won't render any page
@movies_bp.route("/api/update", methods=['POST'])
def post_update_movie():
    rq = request.form
    id = rq.get('movie_id')
    langs = rq.getlist('langs[]')

    movie = Movie.query.get(id)

    # deleteLang = text("DELETE FROM movies_has_languages WHERE movies_id = :id")
    # db.session.execute(deleteLang, {"id": id})
    #
    # for i in langs:
    #     sql = text("INSERT INTO movies_has_languages (movies_id, languages_id) VALUES (:movies_id, :languages_id)")
    #     db.session.execute(sql, {"movies_id": id, "languages_id": i})
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
    # sql = text('''
    #     SELECT
    #         m.*,
    #         GROUP_CONCAT(DISTINCT CONCAT(l.id, ':', l.name) ORDER BY l.name) AS languages,
    #         GROUP_CONCAT(DISTINCT g.name) AS genres
    #     FROM
    #         movies m
    #     LEFT JOIN
    #         movies_has_languages ml ON m.id = ml.movies_id
    #     LEFT JOIN
    #         languages l ON ml.languages_id = l.id
    #     LEFT JOIN
    #         movies_has_genres mg ON m.id = mg.movies_id
    #     LEFT JOIN
    #         genres g ON mg.genres_id = g.id
    #     WHERE m.id = :id
    # ''')
    # result = db.session.execute(sql, {"id": id})
    # movie = result.fetchone()
    # languages = all_languages()
    printed_langs = []
    if movie is None:
        flash('Movie not found', 'error')
        return redirect(url_for('index.index'))

    return render_template('movie/update.html', movie=movie)

