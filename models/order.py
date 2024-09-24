from config.dbConnect import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantity = db.Column(db.Integer, nullable=False)
    order_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                server_default=db.func.current_timestamp())
    total_price = db.Column(db.Numeric(10, 0), nullable=False)

    # Foreign key relationship
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # Relationship with the User model
    user = db.relationship('User', backref=db.backref('orders', cascade="all, delete-orphan", lazy=True))