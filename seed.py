import json
import os
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app
from models import Book, Mood, User, db

DATA_DIR = Path(__file__).parent / "data"


def init_db(app):
    """Create tables and seed data if the database is empty.

    Safe to call multiple times: if moods already exist we assume the DB is
    seeded and skip. This is what entrypoint.sh runs on first container start.
    """
    with app.app_context():
        db.create_all()

        if Mood.query.first():
            print("Database already seeded - skipping.")
            return

        moods_by_code: dict[str, Mood] = {}
        for item in json.loads((DATA_DIR / "moods.json").read_text(encoding="utf-8")):
            mood = Mood(
                code=item["code"],
                name_ru=item["name_ru"],
                emoji=item.get("emoji", ""),
                description=item.get("description", ""),
            )
            db.session.add(mood)
            moods_by_code[mood.code] = mood
        db.session.flush()

        for item in json.loads((DATA_DIR / "books.json").read_text(encoding="utf-8")):
            book = Book(
                title=item["title"],
                author=item["author"],
                year=item.get("year"),
                description=item.get("description", ""),
                language=item.get("language", "ru"),
                cover_url=item.get("cover_url"),
            )
            for code in item.get("moods", []):
                if code in moods_by_code:
                    book.moods.append(moods_by_code[code])
            db.session.add(book)

        admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
        if admin_password == "admin":
            print("WARNING: Using default admin password 'admin'. Set ADMIN_PASSWORD for production.")
        admin = User(
            username="admin",
            password_hash=generate_password_hash(admin_password),
            role="admin",
        )
        db.session.add(admin)

        db.session.commit()
        print(f"Seeded {Mood.query.count()} moods, {Book.query.count()} books, admin user created.")


def reset_db(app):
    """Drop and recreate all tables, then seed. DESTROYS ALL DATA."""
    with app.app_context():
        db.drop_all()
    init_db(app)


if __name__ == "__main__":
    _app = create_app()
    if "--reset" in sys.argv:
        print("WARNING: Dropping all tables and re-seeding...")
        reset_db(_app)
    else:
        init_db(_app)
