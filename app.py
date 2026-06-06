import os
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

from models import Book, Mood, Rating, Recommendation, User, db

BASE_DIR = Path(__file__).parent

csrf = CSRFProtect()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    db_path = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'app.db'}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    csrf.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Войдите, чтобы продолжить."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        moods = _all_moods()
        return render_template("index.html", moods=moods)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            if not username or not password:
                flash("Введите имя пользователя и пароль", "danger")
            elif len(password) < 4:
                flash("Пароль должен быть не короче 4 символов", "danger")
            elif (User.query.filter_by(username=username).first()):
                flash("Такое имя уже занято.", "danger")
            else:
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    role="user",
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Регистрация прошла успешно!", "success")
                return redirect(url_for("index"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Здравствуйте!", "success")
                next_url = request.args.get("next", "")
                if urlparse(next_url).netloc:
                    next_url = ""
                return redirect(next_url or url_for("index"))
            flash("Неверное имя пользователя или пароль.", "danger")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("Вы вышли из системы.", "info")
        return redirect(url_for("index"))

    @app.route("/recommend", methods=["POST"])
    @login_required
    def recommend():
        mood_id = request.form.get("mood_id", type=int)
        mood = db.session.get(Mood, mood_id)
        if mood is None:
            flash("Выберите настроение.", "warning")
            return redirect(url_for("index"))

        books = (
            Book.query
            .join(Book.moods)
            .filter(Mood.id == mood.id)
            .order_by(func.random())
            .limit(5)
            .all()
        )

        rec = Recommendation(user_id=current_user.id, mood_id=mood.id)
        db.session.add(rec)
        db.session.commit()

        return render_template("recommend.html", mood=mood, books=books)

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
        ratings = (
            Rating.query.filter_by(book_id=book.id)
            .options(joinedload(Rating.user))
            .order_by(Rating.created_at.desc())
            .all()
        )
        avg = (sum(r.rating for r in ratings) / len(ratings)) if ratings else None
        my_rating = None
        if current_user.is_authenticated:
            my_rating = Rating.query.filter_by(
                book_id=book.id, user_id=current_user.id
            ).first()
        return render_template(
            "book_detail.html",
            book=book,
            ratings=ratings,
            avg=avg,
            my_rating=my_rating,
        )

    @app.route("/books/<int:book_id>/rate", methods=["POST"])
    @login_required
    def rate_book(book_id):
        book = db.get_or_404(Book, book_id)
        value = request.form.get("rating", type=int) or 0
        comment = (request.form.get("comment") or "").strip()
        if not 1 <= value <= 5:
            flash("Оценка должна быть от 1 до 5.", "danger")
            return redirect(url_for("book_detail", book_id=book.id))

        existing = Rating.query.filter_by(book_id=book.id, user_id=current_user.id).first()
        if existing:
            existing.rating = value
            existing.comment = comment
        else:
            db.session.add(
                Rating(
                    book_id=book.id,
                    user_id=current_user.id,
                    rating=value,
                    comment=comment,
                )
            )
        db.session.commit()

        flash("Спасибо за оценку!", "success")
        return redirect(url_for("book_detail", book_id=book.id))
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        recs = (
            Recommendation.query.filter_by(user_id=current_user.id)
            .options(joinedload(Recommendation.mood))
            .order_by(Recommendation.created_at.desc())
            .limit(50)
            .all()
        )
        ratings = (
            Rating.query.filter_by(user_id=current_user.id)
            .options(joinedload(Rating.book))
            .order_by(Rating.created_at.desc())
            .limit(100)
            .all()
        )
        return render_template("dashboard.html", recs=recs, ratings=ratings)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404


def _all_moods():
    return Mood.query.order_by(Mood.id).all()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
