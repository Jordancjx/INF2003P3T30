from config.dbConnect import db
from datetime import datetime


class Thread(db.Model):
    __tablename__ = 'threads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.func.current_timestamp())
    edited = db.Column(db.Integer, nullable=False, default=0)
    edited_time = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, server_default=db.func.current_timestamp())

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    posted_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.func.current_timestamp())
    edited = db.Column(db.Integer, nullable=True, default=0)
    edited_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, server_default=db.func.current_timestamp())
    
