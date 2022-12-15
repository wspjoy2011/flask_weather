from flask_login import LoginManager


def create_login_manager():
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    return login_manager


login_manager = create_login_manager()
