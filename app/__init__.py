import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        from app import routes  # noqa: F401
        from app.migrate import migrate_db

        db.create_all()
        migrate_db()

    app.register_blueprint(routes.bp)
    return app
