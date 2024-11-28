import asyncio
import datetime

from flask import Flask
from flask_toastr import Toastr
from datetime import timedelta
from config.dbConnect import get_db
from controllers.movie import movies_bp
from controllers.index import index_bp
from controllers.admin import admin_bp
from controllers.user import user_bp
from controllers.review import reviews_bp
from controllers.orders import orders_bp
from controllers.purchases import purchases_bp
from controllers.rental import rentals_bp
from controllers.forum import forum_bp


import config.constants

app = Flask(__name__, template_folder=config.constants.template_dir, static_folder=config.constants.static_dir,
            static_url_path='/public')

# Init toastr
toastr = Toastr(app)


async def setup_indexes():
    db = await get_db()

    await db.Movies.create_index([("_id", 1)])  # Default index on _id
    await db.Movies.create_index([("title", 1)])  # Index for title
    await db.Movies.create_index([("users_id", 1)])  # Index for title

    await db.reviews.create_index([("movies_id", 1)])  # Index for movies_id
    await db.reviews.create_index([("users_id", 1)])  # Index for users_id

    await db.threads.create_index([("_id", 1)])  # Default index
    await db.threads.create_index([("users_id", 1)])  # Index for users creating threads

    await db.posts.create_index([("thread_id", 1)])  # Index for post related to thread
    await db.posts.create_index([("users_id", 1)])  # Index for users_id

    await db.orders.create_index([("movie_id", 1)])  # Index movie_id
    await db.orders.create_index([("users_id", 1)])  # Index for users_id

    print("Indexes created successfully!")


# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(movies_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(purchases_bp)
app.register_blueprint(rentals_bp)
app.register_blueprint(forum_bp)


@app.template_filter('format_datetime')
def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    return value


if __name__ == '__main__':
    # App config
    app.debug = True
    app.permanent_session_lifetime = timedelta(hours=2)
    app.secret_key = config.constants.app_secret_key

    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(setup_indexes())
    else:
        loop.run_until_complete(setup_indexes())
    
    app.run()
