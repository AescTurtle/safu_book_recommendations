from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow() -> datetime:
    """Timezone-aware UTC 'now', used as the default for created_at columns."""
    return datetime.now(timezone.utc)


book_moods = db.Table(
    "book_moods",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    db.Column("mood_id", db.Integer, db.ForeignKey("moods.id", ondelete="CASCADE"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    recommendations = db.relationship("Recommendation", backref="user", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", backref="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Mood(db.Model):
    __tablename__ = "moods"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    name_ru = db.Column(db.String(64), nullable=False)
    emoji = db.Column(db.String(8), nullable=False, default="")
    description = db.Column(db.String(255), nullable=False, default="")

    books = db.relationship("Book", secondary=book_moods, back_populates="moods")


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False, default="")
    language = db.Column(db.String(8), nullable=False, default="ru")
    cover_url = db.Column(db.String(500))

    moods = db.relationship("Mood", secondary=book_moods, back_populates="books")
    ratings = db.relationship("Rating", backref="book", cascade="all, delete-orphan")


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mood_id = db.Column(db.Integer, db.ForeignKey("moods.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    mood = db.relationship("Mood")

    __table_args__ = (db.Index("ix_recommendations_user_id", "user_id"),)


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "book_id", name="uq_user_book_rating"),
        db.Index("ix_ratings_book_id", "book_id"),
    )
