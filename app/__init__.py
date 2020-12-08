from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import googlemaps
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main_bp.login'
gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY", default='AIza_KEY_HERE'))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
