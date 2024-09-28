from config.dbConnect import db
from datetime import datetime


class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    synopsis = db.Column(db.Text, nullable=False)
    release_date = db.Column(db.String(255), nullable=False)
    runtime = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 0), default=0)
    image_url = db.Column(db.Text)
    trailer_link = db.Column(db.String(255), nullable=True)
    imdb_id = db.Column(db.Integer, nullable=True)
    tmdb_id = db.Column(db.Integer, nullable=True)
    purchases = db.Column(db.Integer, default=0)
    language = db.Column(db.Text, nullable=True)
    genre = db.Column(db.Text, nullable=True)
