from config.dbConnect import db
from datetime import datetime

class Purchases(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_number = db.Column(db.String(16), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)  # Format: MM/YY
    full_name = db.Column(db.String(100), nullable=False)
    card_pin = db.Column(db.String(4), nullable=False)  # Simulating a 4-digit PIN
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    purchase_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with the User model (assuming you have a User model)
    user = db.relationship('User', backref=db.backref('purchases', lazy=True))

    def __init__(self, card_number, expiry_date, full_name, card_pin, amount, users_id):
        self.card_number = card_number
        self.expiry_date = expiry_date
        self.full_name = full_name
        self.card_pin = card_pin
        self.amount = amount
        self.users_id = users_id


class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id', ondelete='CASCADE'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    movie_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationship to the `Purchases` model
    purchase = db.relationship('Purchases', backref='history_items')