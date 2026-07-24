"""Test auth endpoints: register, login, me, refresh."""


class TestAuth:
    def test_register(self, client):
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["user"]["username"] == "newuser"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_duplicate(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "dup",
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "dup",
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 409

    def test_login(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "password123",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["username"] == "loginuser"
        assert "access_token" in data

    def test_login_bad_password(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "badpw",
                "email": "badpw@example.com",
                "password": "password123",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "badpw@example.com",
                "password": "wrongpassword",
            },
        )
        assert resp.status_code == 401

    def test_me(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["username"] == "testuser"

    def test_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_update_me(self, client, auth_headers):
        resp = client.patch(
            "/api/auth/me",
            json={
                "display_name": "New Name",
                "bio": "Hello world",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["display_name"] == "New Name"
        assert data["user"]["bio"] == "Hello world"
