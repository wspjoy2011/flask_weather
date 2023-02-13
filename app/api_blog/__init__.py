from flask import Blueprint

api_blog = Blueprint('api_blog', __name__, url_prefix='/api_blog/v1')

from app.api_blog import authentication, posts, users, comments
