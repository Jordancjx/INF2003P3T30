from flask import Flask, request, jsonify, render_template, json
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Update this to your credentials for local sql
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/mydb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Retrieve all Languages
def all_languages():
    sql = text('SELECT * FROM languages')
    result = db.session.execute(sql)
    languages = []
    
    return [{
        'id': row[0],
        'name': row[1]
    } for row in result]


# Retrieve all Movies
def retrieve_all():
    sql = text('''
        SELECT 
            m.id AS movie_id, 
            m.name AS title, 
            m.synopsis, 
            m.price, 
            m.release_date, 
            m.image_url, 
            m.runtime,
            m.price,
            GROUP_CONCAT(DISTINCT l.name) AS languages,
            GROUP_CONCAT(DISTINCT g.name) AS genres,
            AVG(r.rating) AS average_rating,
            COUNT(DISTINCT r.id) AS total_reviews 
        FROM 
            movies m
        LEFT JOIN 
            movies_has_languages ml ON m.id = ml.movies_id
        LEFT JOIN 
            languages l ON ml.languages_id = l.id
        LEFT JOIN 
            movies_has_genres mg ON m.id = mg.movies_id
        LEFT JOIN 
            genres g ON mg.genres_id = g.id
        LEFT JOIN 
            reviews r ON m.id = r.movies_id
        GROUP BY 
            m.id
    ''')
    movies = db.session.execute(sql)
    return [{
        'id': movie.movie_id,
        'title': movie.title,
        'synopsis': movie.synopsis,
        'price': movie.price,
        'release_date': movie.release_date,
        'runtime': movie.runtime,
        'price': movie.price,
        'image_url': movie.image_url,
        'total_reviews' : movie.total_reviews,
        'average_rating' : movie.average_rating,
        'languages': movie.languages.split(',') if movie.languages else [],
        'genres': movie.genres.split(',') if movie.genres else []
    } for movie in movies]

#Index page; Currently displaying all movies
@app.route("/")
def moviesIndex():
    movies = retrieve_all()
    return render_template('index.html', movies = movies)

@app.route("/movie/single/<int:id>", methods = ['GET'])
def singleMovie(id):
    sql = text('''
        SELECT 
            m.*,
            GROUP_CONCAT(DISTINCT l.name) AS languages,
            GROUP_CONCAT(DISTINCT g.name) AS genres,
            AVG(r.rating) AS average_rating,
            COUNT(DISTINCT r.id) AS total_reviews,
            (SELECT JSON_ARRAYAGG(JSON_OBJECT('rating', r2.rating, 'user_id', r2.users_id, 'body', r2.body)) 
            FROM reviews r2 
            WHERE r2.movies_id = m.id) AS reviews
        FROM 
            movies m
        LEFT JOIN 
            movies_has_languages ml ON m.id = ml.movies_id
        LEFT JOIN 
            languages l ON ml.languages_id = l.id
        LEFT JOIN 
            movies_has_genres mg ON m.id = mg.movies_id
        LEFT JOIN 
            genres g ON mg.genres_id = g.id
        LEFT JOIN 
            reviews r ON m.id = r.movies_id
        WHERE m.id = :id
    ''')
    
    result = db.session.execute(sql, {"id": id})
    movie = result.fetchone()
    if movie.reviews:
        reviews = json.loads(movie.reviews)
    else:
        reviews = []
    return render_template('single.html', movie = movie, reviews = reviews)

#Api to delete movies, won't render any page
@app.route("/api/movie/delete/<int:id>", methods = ['DELETE'])
def deleteMovie(id):
    sql = text("DELETE FROM movies WHERE id = :id")
    result = db.session.execute(sql, {"id": id})
    
    # Commit the transaction
    db.session.commit()
    
    #If Movie is not found
    if result.rowcount == 0:
        return jsonify({'error': 'Movie not found'}), 404   
     
    return jsonify({'message': result.rowcount}), 200

#Api to update movies, won't render any page
@app.route("/api/movie/update", methods = ['POST'])
def updateMovie():
    rq = request.form
    id = rq.get('movie_id')
    langs = rq.getlist('langs[]')
    
    deleteLang = text("DELETE FROM movies_has_languages WHERE movies_id = :id")
    db.session.execute(deleteLang, {"id": id})
    
    for i in langs:
        sql = text("INSERT INTO movies_has_languages (movies_id, languages_id) VALUES (:movies_id, :languages_id)")
        db.session.execute(sql, {"movies_id": id, "languages_id": i})
    
    updatesql = text("UPDATE movies SET name = :moviename, price = :price, runtime = :runtime, synopsis = :synopsis, release_date = :release_date, trailer_link = :trailer_link WHERE id = :id")
    db.session.execute(updatesql, {"id": id, "moviename": rq.get('moviename'), "price": rq.get('price'), "runtime" : rq.get('runtime'), "release_date": rq.get('release_date'), "trailer_link":rq.get("trailer_link"), "synopsis":rq.get("synopsis")})
    
    db.session.commit()
    
    return jsonify({'Success': 'Movie Updated'}) 

@app.route('/update_movie/<int:id>')
def update_movie(id):
    sql = text('''
        SELECT 
            m.*,
            GROUP_CONCAT(DISTINCT CONCAT(l.id, ':', l.name) ORDER BY l.name) AS languages,
            GROUP_CONCAT(DISTINCT g.name) AS genres
        FROM 
            movies m
        LEFT JOIN 
            movies_has_languages ml ON m.id = ml.movies_id
        LEFT JOIN 
            languages l ON ml.languages_id = l.id
        LEFT JOIN 
            movies_has_genres mg ON m.id = mg.movies_id
        LEFT JOIN 
            genres g ON mg.genres_id = g.id
        WHERE m.id = :id
    ''')
    result = db.session.execute(sql, {"id": id})
    movie = result.fetchone()
    languages = all_languages()
    printed_langs = []
    return render_template('update_movie.html', movie = movie, printed_langs=printed_langs, languages = languages)



if __name__ == '__main__':
    app.run(debug=True)