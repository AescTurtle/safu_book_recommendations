"""Тесты регистрации, входа и выхода."""

from models import User


def test_register_creates_user(client, app):
    resp = client.post(
        "/register",
        data={"username": "newbie", "password": "secret1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username="newbie").first() is not None


def test_register_duplicate_username(client, app):
    with app.app_context():
        before = User.query.count()
    resp = client.post(
        "/register",
        data={"username": "user1", "password": "secret1"},
        follow_redirects=True,
    )
    assert "занято".encode() in resp.data
    with app.app_context():
        assert User.query.count() == before


def test_register_short_password(client, app):
    with app.app_context():
        before = User.query.count()
    client.post(
        "/register",
        data={"username": "shorty", "password": "ab"},
        follow_redirects=True,
    )
    with app.app_context():
        assert User.query.count() == before


def test_login_wrong_password(client):
    resp = client.post(
        "/login",
        data={"username": "user1", "password": "WRONG"},
        follow_redirects=True,
    )
    assert "Неверное".encode() in resp.data


def test_login_success(login):
    resp = login("user1", "pass1234")
    assert resp.status_code == 200
    assert "user1".encode() in resp.data  # имя пользователя в шапке


def test_logout(client, login):
    login("user1", "pass1234")
    resp = client.post("/logout", follow_redirects=True)
    assert resp.status_code == 200
