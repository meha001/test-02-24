import json
import os
import urllib.error
import urllib.parse
import urllib.request

from sqlalchemy import event

BLOB_PATHNAME = "prizes.db"
API_BASE = "https://blob.vercel-storage.com"
API_VERSION = "10"


def blob_enabled() -> bool:
    return bool(os.environ.get("BLOB_READ_WRITE_TOKEN")) and not os.environ.get("DATABASE_URL")


def sqlite_path_from_uri(uri: str) -> str | None:
    if not uri.startswith("sqlite"):
        return None
    if uri.startswith("sqlite:////"):
        return uri[11:]
    if uri.startswith("sqlite:///"):
        return uri[10:]
    return None


def _auth_headers() -> dict:
    return {
        "authorization": f"Bearer {os.environ['BLOB_READ_WRITE_TOKEN']}",
        "x-api-version": API_VERSION,
    }


def restore_sqlite(db_path: str) -> None:
    if not blob_enabled():
        return
    try:
        query = urllib.parse.urlencode({"prefix": BLOB_PATHNAME, "limit": "1"})
        req = urllib.request.Request(f"{API_BASE}?{query}", headers=_auth_headers(), method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            listing = json.loads(resp.read().decode())
        blobs = listing.get("blobs") or []
        if not blobs:
            return
        dl_req = urllib.request.Request(f"{blobs[0]['url']}?download=1", method="GET")
        with urllib.request.urlopen(dl_req, timeout=30) as resp:
            data = resp.read()
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(db_path, "wb") as f:
            f.write(data)
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
        pass


def persist_sqlite(db_path: str) -> None:
    if not blob_enabled() or not os.path.isfile(db_path):
        return
    try:
        with open(db_path, "rb") as f:
            data = f.read()
        pathname = urllib.parse.quote(BLOB_PATHNAME, safe="")
        headers = {
            **_auth_headers(),
            "x-content-type": "application/x-sqlite3",
            "x-allow-overwrite": "1",
            "access": "public",
        }
        req = urllib.request.Request(
            f"{API_BASE}/?pathname={pathname}",
            data=data,
            headers=headers,
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=30)
    except (urllib.error.URLError, OSError):
        pass


def register_persist_hook(db, db_path: str | None) -> None:
    if not db_path or not blob_enabled():
        return

    @event.listens_for(db.session, "after_commit")
    def _persist_after_commit(session):
        persist_sqlite(db_path)
