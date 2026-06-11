"""Тесты администрирования: доступ, CRUD книг, экспорт CSV."""

from models import Book, db


def test_admin_requires_login(client):
    resp = client.get("/admin")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_forbidden_for_regular_user(client, login):
    login("user1", "pass1234")
    resp = client.get("/admin")
    assert resp.status_code == 403


def test_admin_dashboard_ok(client, login):
    login("admin1", "admin1234")
    resp = client.get("/admin")
    assert resp.status_code == 200


def test_admin_list_books(client, login):
    login("admin1", "admin1234")
    resp = client.get("/admin/books")
    assert resp.status_code == 200
    assert "Тестовая книга".encode() in resp.data


def test_admin_create_book(client, login, app):
    login("admin1", "admin1234")
    resp = client.post(
        "/admin/books/new",
        data={"title": "Новинка", "author": "Кто-то", "language": "ru"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert Book.query.filter_by(title="Новинка").first() is not None


def test_admin_create_book_requires_title(client, login, app):
    login("admin1", "admin1234")
    with app.app_context():
        before = Book.query.count()
    client.post(
        "/admin/books/new",
        data={"title": "", "author": "Кто-то"},
        follow_redirects=True,
    )
    with app.app_context():
        assert Book.query.count() == before


def test_admin_edit_book(client, login, app):
    login("admin1", "admin1234")
    with app.app_context():
        book_id = Book.query.first().id
    client.post(
        f"/admin/books/{book_id}/edit",
        data={"title": "Изменено", "author": "Автор", "language": "ru"},
        follow_redirects=True,
    )
    with app.app_context():
        assert db.session.get(Book, book_id).title == "Изменено"


def test_admin_delete_book(client, login, app):
    login("admin1", "admin1234")
    with app.app_context():
        book_id = Book.query.first().id
    client.post(f"/admin/books/{book_id}/delete", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Book, book_id) is None


def test_export_books_csv(client, login):
    login("admin1", "admin1234")
    resp = client.get("/admin/export/books.csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "title,author,year,language,moods" in resp.data.decode("utf-8")


def test_export_recommendations_csv(client, login):
    login("admin1", "admin1234")
    resp = client.get("/admin/export/recommendations.csv")
    assert resp.status_code == 200
    assert "user,mood_code,mood_ru" in resp.data.decode("utf-8")
