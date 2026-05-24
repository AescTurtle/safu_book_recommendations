import os
from pathlib import Path

from flask import Flask, render_template

from models import db

BASE_DIR = Path(__file__).parent


def create_app() -> Flask:
    """Application factory: build and configure the Flask app, then return it.

    Using a factory (instead of a module-level ``app = Flask(...)``) lets tests
    create a fresh, isolated app with their own config, and keeps importing this
    module free of side effects.
    """
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
        return render_template("index.html")


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
