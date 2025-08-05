from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()  # <- force load environment before anything else

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .routes import main
from flask_wtf import CSRFProtect
from .models import db

login_manager = LoginManager()
login_manager.login_view = 'main.login'



def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(main)

    # --- CSRF error handler ---
    from flask_wtf.csrf import CSRFError
    from .routes import LoginForm
    from flask import render_template, flash
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('CSRF token missing or invalid. Please refresh the page and try again.', 'error')
        return render_template('login.html', form=LoginForm()), 400

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

