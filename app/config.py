import os
from dotenv import load_dotenv

from definitions import PATH_TO_ENV_FILE

load_dotenv(PATH_TO_ENV_FILE)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    DB_NAME = os.getenv('DATABASE')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    UPLOAD_FOLDER = os.path.join('app', 'static', 'img', 'profile')
    UPLOAD_URL = '/static/img/profile/'
    ALLOWED_EXTENSIONS = {'png', 'jpeg', 'gif'}

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.urandom(32)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
