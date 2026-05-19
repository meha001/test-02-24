from sqlalchemy import inspect, text

from app import db
from app.models import Giveaway
from app.services import generate_public_token


def migrate_db():
    inspector = inspect(db.engine)
    if "giveaways" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("giveaways")}
    if "public_token" not in columns:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE giveaways ADD COLUMN public_token VARCHAR(32)"))

    missing = Giveaway.query.filter(
        (Giveaway.public_token.is_(None)) | (Giveaway.public_token == "")
    ).all()
    for giveaway in missing:
        giveaway.public_token = generate_public_token()

    if missing:
        db.session.commit()
