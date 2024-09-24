from config.dbConnect import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    body = db.Column(db.Text, nullable=False)
    written_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                             server_default=db.func.current_timestamp())
    rating = db.Column(db.Integer, nullable=False)

    # Foreign key relationships
    movies_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete="CASCADE", onupdate="CASCADE"),
                          nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # Relationships with other models
    movie = db.relationship('Movie', backref=db.backref('reviews', cascade="all, delete-orphan", lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', cascade="all, delete-orphan", lazy=True))
