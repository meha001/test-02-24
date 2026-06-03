import os

from flask import Flask, flash, redirect, url_for
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
        from app.db_storage import register_persist_hook, restore_sqlite, sqlite_path_from_uri
        from app.migrate import migrate_db

        db_path = sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])
        if db_path:
            restore_sqlite(db_path)

        db.create_all()
        migrate_db()
        register_persist_hook(db, db_path)

    app.register_blueprint(routes.bp)

    @app.errorhandler(404)
    def not_found(_error):
        flash(
            "Страница или розыгрыш не найдены. На Vercel подключите Blob-хранилище "
            "или задайте DATABASE_URL для постоянной базы данных.",
            "error",
        )
        return redirect(url_for("main.index"))

    return app
