from flask import Blueprint

blog = Blueprint('blog', __name__, url_prefix='/blog')

from app.blog import routes
