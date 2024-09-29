from config.dbConnect import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.func.current_timestamp())
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Foreign key relationships
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # Relationships with Movie and User models
    movie = db.relationship('Movie', backref=db.backref('orders', cascade="all, delete-orphan", lazy=True))
    user = db.relationship('User', backref=db.backref('orders', cascade="all, delete-orphan", lazy=True))
