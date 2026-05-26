import os
from pathlib import Path

from flask import Flask, render_template

from models import Mood, db

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


def _all_moods():
    """All moods in a stable order (by id), for the home page and filters."""
    return Mood.query.order_by(Mood.id).all()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
