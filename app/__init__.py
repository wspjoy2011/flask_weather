from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from peewee import SqliteDatabase
from flask_pagedown import PageDown

from app.config import config
from app.error_handlers import page_not_found, internal_server_error
from app.base_model import database_proxy
from app.auth.utils import login_manager
from app.api.weather.cities import init_app as init_app_cities
from app.api.weather.city import init_app as init_app_city
from app.api.weather.countries import init_app as init_app_countries
from app.api.weather.country import init_app as init_app_country
from app.auth.models import User, Role, Profile, Follow
from app.weather.models import Country, City, UserCity
from app.blog.models import Post


def create_app(config_name='default'):
    app = Flask(__name__)
    app.static_folder = 'static'
    app.config.from_object(config[config_name])

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    if config_name == 'testing':
        db = SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})
    else:
        db = SqliteDatabase(app.config['DB_NAME'], pragmas={'foreign_keys': 1})

    database_proxy.initialize(db)
    db.create_tables(
        [Role, Profile, User, Country, City, UserCity, Post, Follow]
    )

    app.config['db'] = db

    login_manager.init_app(app)

    csrf = CSRFProtect(app)
    csrf.init_app(app)
    app.config['CSRF'] = csrf

    pagedown = PageDown()
    pagedown.init_app(app)

    init_app_cities(app)
    init_app_city(app)
    init_app_countries(app)
    init_app_country(app)

    Bootstrap(app)

    moment = Moment(app)
    moment.init_app(app)

    from app import main
    from app import weather
    from app import auth
    from app import blog

    app.register_blueprint(main.main)
    app.register_blueprint(weather.weather)
    app.register_blueprint(auth.auth)
    app.register_blueprint(blog.blog)

    return app
