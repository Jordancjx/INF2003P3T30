import os

app_secret_key = '12345'
template_dir = os.path.abspath('views')
static_dir = os.path.abspath('public')
database_path = os.path.abspath('data')
database_file = os.path.join(database_path, 'movieDB.db')
