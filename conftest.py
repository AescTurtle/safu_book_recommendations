"""Общие фикстуры pytest.

Каждый тест получает свежее приложение с отдельной временной базой SQLite
(файл, а не in-memory — чтобы все соединения тест-клиента видели одни данные)
и отключённой CSRF-защитой, чтобы можно было отправлять формы без токена.
"""

import os
import tempfile

import pytest


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("SECRET_KEY", "test-secret")

    from app import create_app
    from models import Book, Mood, User, db
    from werkzeug.security import generate_password_hash

    application = create_app()
    application.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with application.app_context():
        db.create_all()

        calm = Mood(code="calm", name_ru="Спокойствие", emoji="😌", description="тихо")
        joy = Mood(code="joy", name_ru="Радость", emoji="😄", description="светло")
        b1 = Book(title="Тестовая книга", author="Автор Один", year=2000, language="ru")
        b2 = Book(title="Вторая книга", author="Автор Два", language="ru")
        b1.moods = [calm]
        b2.moods = [joy]
        user = User(username="user1", password_hash=generate_password_hash("pass1234"), role="user")
        admin = User(username="admin1", password_hash=generate_password_hash("admin1234"), role="admin")
        db.session.add_all([calm, joy, b1, b2, user, admin])
        db.session.commit()

    yield application

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    """Возвращает функцию входа: login(username, password)."""

    def _login(username, password):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    return _login
