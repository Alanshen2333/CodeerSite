"""Issue #29: JWT 吊销写/查闭环与退出端点。"""


class TestJWTBlocklist:
    def _login(self, client):
        client.post(
            "/api/auth/register",
            json={
                "username": "logoutuser",
                "email": "logout@example.com",
                "password": "password123",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={"email": "logout@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        return resp.get_json()

    def test_logout_revokes_access_token(self, client):
        tokens = self._login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post("/api/auth/logout", headers=headers)
        assert resp.status_code == 200

        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 401

    def test_logout_revokes_refresh_token_when_provided(self, client):
        tokens = self._login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        assert resp.status_code == 200

        refresh_headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
        resp = client.post("/api/auth/refresh", headers=refresh_headers)
        assert resp.status_code == 401

    def test_logout_requires_auth(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401
