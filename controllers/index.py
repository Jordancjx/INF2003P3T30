from flask import Blueprint, render_template, request, redirect, url_for, current_app
import config.constants
from sqlalchemy import text
from models.movie import Movie
from config.dbConnect import db


index_bp = Blueprint('index', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/')


@index_bp.route('/')
def index():
    with current_app.app_context():
        sql=text("SELECT * FROM movies LIMIT 10")
        result=db.session.execute(sql)
        movies=result.fetchall()
        
    return render_template('index.html', movies=movies)
