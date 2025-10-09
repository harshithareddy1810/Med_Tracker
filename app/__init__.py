# app/__init__.py
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' # Redirect to login page if not authenticated

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
# Add this to app/__init__.py after login_manager is initialized
from .models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))