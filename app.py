from flask import Flask
from flask_pymongo import PyMongo
from flask_toastr import Toastr
from datetime import timedelta
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

# Setup DB
app.config['MONGO_URI'] = config.constants.mongo_uri
mongo = PyMongo(app)

app.mongo = mongo  # Adding mongo to the app instance to resolve AttributeError

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

if __name__ == '__main__':
    # App config
    app.debug = True
    app.permanent_session_lifetime = timedelta(hours=2)
    app.secret_key = config.constants.app_secret_key

    app.run()
