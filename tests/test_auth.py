from io import BytesIO

from yatrago import db
from yatrago.models import User


def test_authentication_pages_show_distinct_indian_travel_photographs(client):
    login = client.get("/auth/login")
    register = client.get("/auth/register")
    assert login.status_code == register.status_code == 200
    assert b"photo-1470770841072-f978cf4d019e" in login.data
    assert b"mountain lake" in login.data
    assert b"photo-1464822759023-fed622ff2c3b" in register.data
    assert b"Himalayan mountains" in register.data


def test_registration_hashes_password_and_signs_in(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Asha Rao",
            "email": "ASHA@example.com",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your YatraGo account is ready" in response.data
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "asha@example.com"))
        assert user is not None
        assert user.password_hash != "secure-pass-123"
        assert user.check_password("secure-pass-123")


def test_registration_rejects_invalid_email_and_mismatched_passwords(client):
    response = client.post(
        "/auth/register",
        data={
            "name": "Asha",
            "email": "not-an-email",
            "password": "secure-pass-123",
            "confirm_password": "different-pass",
        },
    )
    assert response.status_code == 200
    assert b"Enter a valid email address" in response.data


def test_login_logout_and_protected_dashboard(client):
    client.post(
        "/auth/register",
        data={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
    )
    client.post("/auth/logout")
    response = client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert client.get("/dashboard").status_code == 200
    client.post("/auth/logout")
    assert client.get("/dashboard").status_code == 302


def test_profile_photo_upload_saves_image_and_user_path(client, app, tmp_path):
    app.static_folder = str(tmp_path / "static")
    client.post(
        "/auth/register",
        data={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
    )

    response = client.post(
        "/profile/upload",
        data={"avatar": (BytesIO(b"sample image data"), "profile.jpg")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile photo updated." in response.data
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "asha@example.com"))
        assert user.avatar.startswith("uploads/user_")
        assert (tmp_path / "static" / user.avatar).is_file()


def test_login_rejects_external_next_redirect(client):
    client.post(
        "/auth/register",
        data={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
    )
    client.post("/auth/logout")
    response = client.post(
        "/auth/login?next=https://example.com",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    assert response.headers["Location"].endswith("/dashboard")
