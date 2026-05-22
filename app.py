import os

from flask import Flask, render_template


def create_app() -> Flask:
    """Application factory: build and configure the Flask app, then return it.

    Using a factory (instead of a module-level ``app = Flask(...)``) lets tests
    create a fresh, isolated app with their own config, and keeps importing this
    module free of side effects.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html")


# Module-level app so `flask run` (which looks for `app`) and gunicorn both work.
app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
