import os
from pathlib import Path

from flask import Flask, render_template, request

from models import Book, Mood, db

BASE_DIR = Path(__file__).parent


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db_path = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'app.db'}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        moods = _all_moods()
        return render_template("index.html", moods=moods)

    @app.route("/books")
    def books_list():
        mood_code = request.args.get("mood")
        q = request.args.get("q", "").strip()

        query = Book.query
        if mood_code:
            query = query.join(Book.moods).filter(Mood.code == mood_code)
        if q:
            like = f"%{q}%"
            query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)))
        books = query.order_by(Book.title).all()

        return render_template(
            "books_list.html",
            books=books,
            moods=_all_moods(),
            selected_mood=mood_code,
            q=q,
        )

    @app.route("/books/<int:book_id>")
    def book_detail(book_id):
        book = db.get_or_404(Book, book_id)
        ratings = []
        return render_template("book_detail.html", book=book, ratings=ratings)
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404


def _all_moods():
    """All moods in a stable order (by id), for the home page and filters."""
    return Mood.query.order_by(Mood.id).all()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
