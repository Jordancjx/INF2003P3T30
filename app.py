from flask import Flask
from flask_toastr import Toastr
from datetime import timedelta
from config.dbConnect import db
from controllers.movie import movies_bp
from controllers.index import index_bp
from controllers.admin import admin_bp
from controllers.user import user_bp
from controllers.review import reviews_bp
from controllers.orders import orders_bp
from controllers.purchases import purchases_bp
from controllers.rental import rentals_bp
from controllers.forum import forum_bp
from utilities.movie import clean_insert_movies

import config.constants

app = Flask(__name__, template_folder=config.constants.template_dir, static_folder=config.constants.static_dir,
            static_url_path='/public')

# Setup DB
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config.constants.database_file}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Init toastr
toastr = Toastr(app)

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

from models.movie import Movie
from models.user import User
from models.review import Review
from models.order import Order
from models.purchases import Purchases, History
from models.forum import Thread, Post

with app.app_context():
    # ABSOLUTELY DO NOT UNCOMMENT, TESTING PURPOSES ONLY
    # db.drop_all()
    # Movie.__table__.drop(db.engine)

    # Create tables
    db.create_all()

if __name__ == '__main__':
    # App config
    app.debug = True
    app.permanent_session_lifetime = timedelta(hours=2)
    app.secret_key = config.constants.app_secret_key

    with app.app_context():
        # Insert movies (15-20 min)
        clean_insert_movies()
    app.run()
