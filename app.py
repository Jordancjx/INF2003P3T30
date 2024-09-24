from flask import Flask
from config.dbConnect import db
from controllers.movie import movies_bp
from controllers.index import index_bp

import config.constants

app = Flask(__name__, template_folder=config.constants.template_dir, static_folder=config.constants.static_dir,
            static_url_path='/public')

# Setup DB
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config.constants.database_file}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Register blueprints
app.register_blueprint(index_bp)
app.register_blueprint(movies_bp)

from models.movie import Movie
from models.user import User
from models.review import Review
from models.order import Order

with app.app_context():
    # ABSOLUTELY DO NOT UNCOMMENT, TESTING PURPOSES ONLY
    # db.drop_all()

    # Create tables
    db.create_all()

if __name__ == '__main__':
    app.debug = True
    app.run()
