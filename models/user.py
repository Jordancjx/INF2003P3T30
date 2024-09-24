from config.dbConnect import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(16), nullable=False, unique=True)
    fname = db.Column(db.String(255), nullable=True)
    lname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    profile_pic_url = db.Column(db.Text, nullable=True)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            server_default=db.func.current_timestamp())
    email_validated = db.Column(db.Boolean, nullable=False, default=False)  # Use Boolean for tinyint(1)
    admin_controls = db.Column(db.Boolean, nullable=False, default=False)     # Use Boolean for tinyint(1)
