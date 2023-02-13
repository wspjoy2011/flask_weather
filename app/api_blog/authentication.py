from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from app.api_blog import api_blog
from app.api_blog.errors import unauthorized
from app.auth.models import User

auth_basic = HTTPBasicAuth()


@auth_basic.verify_password
def verify_password(email_or_token, password):
    if not email_or_token:
        return False

    if not password:
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None

    user = User.select().where(User.email == email_or_token).first()
    if not user:
        return False

    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@api_blog.before_request
@auth_basic.login_required
def before_request():
    pass


@auth_basic.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api_blog.route('/tokens/', methods=['GET', 'POST'])
@auth_basic.login_required
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
