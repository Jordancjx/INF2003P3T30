from flask import Blueprint, render_template, request, redirect, url_for
import config.constants
from models.movie import Movie


index_bp = Blueprint('index', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/')


@index_bp.route('/')
def index():
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)
