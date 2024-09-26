import requests
import pandas as pd
from models.movie import Movie
from config.constants import TMDB_API_KEY, tmdb_dataset_file
from config.dbConnect import db

TMDB_BASE_URL = "https://api.themoviedb.org/3/movie/"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def fetch_poster_url(movie_id):
    url = f"{TMDB_BASE_URL}{movie_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"{IMAGE_BASE_URL}{data['poster_path']}" if data['poster_path'] else None
    return None


def clean_and_insert_movies():
    # Load CSV
    df = pd.read_csv(tmdb_dataset_file, sep='|', on_bad_lines='skip',
                     dtype='unicode')

    # new_columns = df.columns[0].split(',')
    # df.columns = new_columns
    print(df.shape)

    # Drop unwanted columns
    df = df.drop(columns=['vote_count', 'status', 'revenue', 'backdrop_path', 'budget', 'homepage',
                          'original_title', 'poster_path', 'tagline', 'production_companies', 'production_countries',
                          'spoken_languages'])
    df.fillna('', inplace=True)

    movies = []
    count = 0

    # Iterate through the dataset and fetch poster URLs
    try:
        for index, row in df.iterrows():
            tmdb_id = row['id']
            poster_url = fetch_poster_url(tmdb_id)
            if poster_url:
                # Look for movies with same tmdb id
                movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()

                # Insert if not exists
                if not movie:
                    movie = Movie(
                        name=row['title'],
                        synopsis=row['overview'],
                        release_date=row['release_date'],
                        runtime=row['runtime'],
                        tmdb_id=tmdb_id,
                        imdb_id=row['imdb_id'],
                        image_url=poster_url
                    )
                    movies.append(movie)
                    count += 1
                    print(f'Movies added: {count}/{len(df)}')

    except Exception as e:
        db.session.rollback()

    # Bulk insert
    db.session.bulk_save_objects(movies)
    db.session.commit()
