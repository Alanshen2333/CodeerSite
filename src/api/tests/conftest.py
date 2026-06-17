import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Create a test Flask app with in-memory SQLite."""
    app = create_app("test")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register and login a test user, return auth headers."""
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    data = resp.get_json()
    return {"Authorization": f"Bearer {data['access_token']}"}
