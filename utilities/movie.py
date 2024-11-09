import asyncio
import aiohttp
import pandas as pd
from models.movie import Movie
from config.constants import TMDB_API_KEY, tmdb_dataset_file
from config.dbConnect import db

TMDB_BASE_URL = "https://api.themoviedb.org/3/movie/"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
DF_SIZE = 2000
CHUNK_SIZE = 1000


async def fetch_poster_url(session, movie_id):
    url = f"{TMDB_BASE_URL}{movie_id}?api_key={TMDB_API_KEY}"
    async with session.get(url) as res:
        data = await res.json()
        return data.get('poster_path', None)


async def insert_movies(df_chunk):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for index, row in df_chunk.iterrows():
            tmdb_id = row['id']
            tasks.append(fetch_poster_url(session, tmdb_id))

        poster_urls = await asyncio.gather(*tasks)

        # Iterate through the dataset and fetch poster URLs
        print("Adding movies...")
        try:
            movies = [Movie(
                name=row.title,
                synopsis=row.overview,
                release_date=row.release_date,
                runtime=row.runtime,
                tmdb_id=row.id,
                imdb_id=row.imdb_id,
                image_url=poster_url if poster_url else None,
                language=row.spoken_languages,
                genre=row.genres
            )
                for row, poster_url in zip(df_chunk.itertuples(), poster_urls)
            ]

            # Bulk insert
            db.session.add_all(movies)
            db.session.commit()

        except Exception as e:
            print(e)
            db.session.rollback()


def clean_insert_movies(chunk_size=CHUNK_SIZE):
    if Movie.query.count() > 0:
        print('Movies exist, aborting insert...')
        return

    # Load CSV
    df = pd.read_csv(tmdb_dataset_file, on_bad_lines='skip', engine='python',
                     dtype='unicode')

    # Drop unwanted columns
    df = df.drop(columns=['vote_count', 'status', 'revenue', 'backdrop_path', 'budget', 'homepage', 'original_language',
                          'original_title', 'poster_path', 'tagline', 'production_companies', 'production_countries',
                          'adult'])
    df = df.head(DF_SIZE)
    df.fillna('', inplace=True)

    num_chunks = len(df) // chunk_size + 1

    for i in range(num_chunks):
        chunk = df[i * chunk_size:(i + 1) * chunk_size]
        print(f"Processing chunk {i + 1}/{num_chunks}")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(insert_movies(chunk))

    print('Movies inserted')
