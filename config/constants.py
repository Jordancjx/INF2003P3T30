import os

app_secret_key = '12345'
template_dir = os.path.abspath('views')
static_dir = os.path.abspath('public')
database_path = os.path.abspath('data')
database_file = os.path.join(database_path, 'movieDB.db')
tmdb_dataset_file = os.path.join(database_path, 'TMDB_dataset.csv')
TMDB_API_KEY = 'fbb6add73e66f1ac2ba7fe8a70f0490f'
