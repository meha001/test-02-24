import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _default_sqlite_uri():
    db_path = os.path.join(BASE_DIR, "prizes.db")
    if not os.access(BASE_DIR, os.W_OK):
        # Serverless runtimes (e.g. AWS Lambda /var/task) are read-only; /tmp is writable.
        db_path = os.path.join("/tmp", "prizes.db")
    return f"sqlite:///{db_path}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-prize-draw-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _default_sqlite_uri())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
