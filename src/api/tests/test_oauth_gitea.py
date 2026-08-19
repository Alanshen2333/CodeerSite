"""Gitea OAuth 绑定/登录 + HTTP Git 凭据测试。"""

from unittest.mock import MagicMock, patch

from app.services.gitea_oauth_service import GiteaOAuthService


class TestOAuthAuthorize:
    def test_authorize_login(self, client, app):
        with app.app_context():
            app.config["GITEA_URL"] = "http://localhost:23000"
            app.config["GITEA_OAUTH_CLIENT_ID"] = "test-client-id"
            app.config["GITEA_OAUTH_CLIENT_SECRET"] = "test-client-secret"
            app.config["GITEA_OAUTH_REDIRECT_URI"] = "http://localhost:3000/oauth/gitea"

        resp = client.get("/api/auth/oauth/gitea/authorize?intent=login")
        assert resp.status_code == 200
        data = resp.get_json()
        url = data["authorization_url"]
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Foauth%2Fgitea" in url
        assert "response_type=code" in url
        assert "state=" in url
        assert "scope=read%3Auser+read%3Arepository+write%3Arepository" in url

    def test_authorize_uses_public_gitea_url(self, client, app):
        with app.app_context():
            app.config["GITEA_URL"] = "http://gitea:3000"
            app.config["GITEA_PUBLIC_URL"] = "http://example.test:28080/gitea"
            app.config["GITEA_OAUTH_CLIENT_ID"] = "test-client-id"

        resp = client.get("/api/auth/oauth/gitea/authorize?intent=login")

        assert resp.status_code == 200
        assert resp.get_json()["authorization_url"].startswith(
            "http://example.test:28080/gitea/login/oauth/authorize?"
        )

    def test_authorize_bind_requires_auth(self, client, app):
        with app.app_context():
            app.config["GITEA_URL"] = "http://localhost:23000"
            app.config["GITEA_OAUTH_CLIENT_ID"] = "test-client-id"
            app.config["GITEA_OAUTH_CLIENT_SECRET"] = "test-client-secret"

        resp = client.get("/api/auth/oauth/gitea/authorize?intent=bind")
        assert resp.status_code == 401


class TestOAuthCallback:
    def _make_state(self, app, intent, user_id=None):
        with app.app_context():
            return GiteaOAuthService._generate_state(intent, user_id)

    @patch("app.services.gitea_oauth_service.GiteaClient")
    def test_callback_login_existing_bound_user(
        self, mock_client, client, app, auth_headers
    ):
        with app.app_context():
            from app.models.user import User

            user = User.query.filter_by(username="testuser").first()
            user.gitea_user_id = "123"
            from app.extensions import db

            db.session.commit()

        mock_client.exchange_oauth_code.return_value = {
            "access_token": "oauth-access-token",
            "refresh_token": "oauth-refresh-token",
            "expires_in": 3600,
        }
        mock_client.get_oauth_user.return_value = {"id": 123, "login": "gituser"}

        state = self._make_state(app, "login")
        resp = client.get("/api/auth/oauth/gitea/callback?code=abc&state=" + state)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["gitea_bound"] is True
        assert "access_token" in data
        assert "refresh_token" in data

    @patch("app.services.gitea_oauth_service.GiteaClient")
    def test_callback_login_unbound_user(self, mock_client, client, app):
        mock_client.exchange_oauth_code.return_value = {
            "access_token": "oauth-access-token",
        }
        mock_client.get_oauth_user.return_value = {"id": 999, "login": "unknown"}

        state = self._make_state(app, "login")
        resp = client.get("/api/auth/oauth/gitea/callback?code=abc&state=" + state)
        assert resp.status_code == 404

    @patch("app.services.gitea_oauth_service.GiteaClient")
    def test_callback_bind(self, mock_client, client, app, auth_headers):
        from app.models.user import User

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user_id = user.id

        mock_client.exchange_oauth_code.return_value = {
            "access_token": "oauth-access-token",
            "refresh_token": "oauth-refresh-token",
            "expires_in": 3600,
        }
        mock_client.get_oauth_user.return_value = {"id": 456, "login": "gituser"}

        state = self._make_state(app, "bind", user_id)
        resp = client.get(
            "/api/auth/oauth/gitea/callback?code=abc&state=" + state,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["gitea_bound"] is True

    @patch("app.services.gitea_oauth_service.GiteaClient")
    def test_callback_bind_already_linked(self, mock_client, client, app, auth_headers):
        from app.models.user import User
        from app.extensions import db
        from app.services.auth_service import AuthService

        with app.app_context():
            other = AuthService.register_user(
                username="otheruser",
                email="other@example.com",
                password="password123",
            )
            other.gitea_user_id = "789"
            db.session.commit()
            current = User.query.filter_by(username="testuser").first()
            current_id = current.id

        mock_client.exchange_oauth_code.return_value = {
            "access_token": "oauth-access-token",
        }
        mock_client.get_oauth_user.return_value = {"id": 789, "login": "alreadylinked"}

        state = self._make_state(app, "bind", current_id)
        resp = client.get(
            "/api/auth/oauth/gitea/callback?code=abc&state=" + state,
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_callback_invalid_state(self, client):
        resp = client.get("/api/auth/oauth/gitea/callback?code=abc&state=invalid-state")
        assert resp.status_code == 400


class TestGitCredentials:
    @patch("app.services.gitea_client.GiteaClient.for_user")
    def test_git_credentials_success(self, mock_for_user, client, app, auth_headers):
        mock_client = MagicMock()
        mock_client._access_token.return_value = "mock-token"
        mock_for_user.return_value = mock_client

        with app.app_context():
            app.config["GITEA_URL"] = "http://localhost:23000"

        resp = client.get(
            "/api/auth/git-credentials?repo=codeersite/test-project",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["clone_url_with_credentials"] == (
            "http://oauth2:mock-token@localhost:23000/codeersite/test-project.git"
        )

    @patch("app.services.gitea_client.GiteaClient.for_user")
    def test_git_credentials_no_token(self, mock_for_user, client, auth_headers):
        mock_for_user.return_value = None

        resp = client.get(
            "/api/auth/git-credentials?repo=codeersite/test-project",
            headers=auth_headers,
        )
        assert resp.status_code == 503
