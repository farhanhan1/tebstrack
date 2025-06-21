from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .routes import main
from .models import db

login_manager = LoginManager()
login_manager.login_view = 'login'


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(main)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

