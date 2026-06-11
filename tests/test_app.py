"""Тесты пользовательских функций: главная, каталог, подбор, оценки, кабинет."""

from models import Book, Mood, Rating, Recommendation


def test_index_lists_moods(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Спокойствие".encode() in resp.data


def test_books_filter_by_mood(client):
    resp = client.get("/books?mood=calm")
    assert resp.status_code == 200
    assert "Тестовая книга".encode() in resp.data
    assert "Вторая книга".encode() not in resp.data


def test_books_search_by_query(client):
    resp = client.get("/books?q=Вторая")
    assert "Вторая книга".encode() in resp.data
    assert "Тестовая книга".encode() not in resp.data


def test_book_detail_ok(client, app):
    with app.app_context():
        book_id = Book.query.first().id
    resp = client.get(f"/books/{book_id}")
    assert resp.status_code == 200


def test_recommend_requires_login(client):
    resp = client.post("/recommend", data={"mood_id": 1})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_recommend_creates_history(client, login, app):
    with app.app_context():
        mood_id = Mood.query.filter_by(code="calm").first().id
    login("user1", "pass1234")
    resp = client.post("/recommend", data={"mood_id": mood_id}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Тестовая книга".encode() in resp.data
    with app.app_context():
        assert Recommendation.query.count() == 1


def test_rate_book_create_then_update(client, login, app):
    with app.app_context():
        book_id = Book.query.first().id
    login("user1", "pass1234")

    client.post(f"/books/{book_id}/rate", data={"rating": 4, "comment": "ок"}, follow_redirects=True)
    with app.app_context():
        rows = Rating.query.filter_by(book_id=book_id).all()
        assert len(rows) == 1 and rows[0].rating == 4

    # повторная отправка обновляет существующую оценку (upsert), не создаёт новую
    client.post(f"/books/{book_id}/rate", data={"rating": 2, "comment": "хуже"}, follow_redirects=True)
    with app.app_context():
        rows = Rating.query.filter_by(book_id=book_id).all()
        assert len(rows) == 1 and rows[0].rating == 2


def test_rate_book_rejects_out_of_range(client, login, app):
    with app.app_context():
        book_id = Book.query.first().id
    login("user1", "pass1234")
    client.post(f"/books/{book_id}/rate", data={"rating": 6}, follow_redirects=True)
    with app.app_context():
        assert Rating.query.count() == 0


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_dashboard_ok_for_user(client, login):
    login("user1", "pass1234")
    resp = client.get("/dashboard")
    assert resp.status_code == 200
