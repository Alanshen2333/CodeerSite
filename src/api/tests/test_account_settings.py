import io
import pytest
from PIL import Image
from app.models.user_ssh_key import UserSshKey
from app.services.email_code_service import EmailCodeService
from app.services.ssh_key_service import SshKeyService


class TestUpdateProfile:
    def test_update_profile_success(self, client, auth_headers):
        resp = client.patch(
            "/api/auth/me",
            json={
                "display_name": "New Name",
                "bio": "Hello world",
                "website": "https://example.com",
                "location": "Beijing",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["display_name"] == "New Name"
        assert data["user"]["bio"] == "Hello world"

    def test_update_profile_requires_auth(self, client):
        resp = client.patch("/api/auth/me", json={"display_name": "x"})
        assert resp.status_code == 401


class TestAvatarUpload:
    def _make_png(self, width: int = 100, height: int = 100):
        """用 Pillow 构造一个有效 PNG。"""
        img = Image.new("RGB", (width, height), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    def test_upload_avatar_success(self, client, auth_headers):
        png = self._make_png()
        resp = client.post(
            "/api/auth/avatar",
            data={"file": (io.BytesIO(png), "avatar.png", "image/png")},
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["avatar_url"].startswith("/api/users/avatar/")

        # 验证可访问
        avatar_resp = client.get(data["avatar_url"])
        assert avatar_resp.status_code == 200
        assert avatar_resp.content_type == "image/png"

    def test_upload_avatar_requires_auth(self, client):
        resp = client.post(
            "/api/auth/avatar",
            data={"file": (io.BytesIO(self._make_png()), "avatar.png", "image/png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 401

    def test_upload_avatar_invalid_format(self, client, auth_headers):
        resp = client.post(
            "/api/auth/avatar",
            data={"file": (io.BytesIO(b"not an image"), "avatar.txt", "text/plain")},
            headers=auth_headers,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


class TestChangePassword:
    def test_change_password_success(self, client, auth_headers):
        # 先请求验证码
        code = EmailCodeService.send_code("test@example.com", "change_password")

        resp = client.post(
            "/api/auth/change-password",
            json={
                "verification_code": code,
                "new_password": "newpassword123",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 使用新密码登录
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "newpassword123"},
        )
        assert login_resp.status_code == 200

    def test_change_password_invalid_code(self, client, auth_headers):
        resp = client.post(
            "/api/auth/change-password",
            json={"verification_code": "000000", "new_password": "newpassword123"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_change_password_requires_auth(self, client):
        resp = client.post(
            "/api/auth/change-password",
            json={"verification_code": "000000", "new_password": "newpassword123"},
        )
        assert resp.status_code == 401


class TestEmailCode:
    def test_request_email_code_success(self, client, auth_headers):
        resp = client.post(
            "/api/auth/email-code",
            json={"purpose": "change_password"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_request_email_code_invalid_purpose(self, client, auth_headers):
        resp = client.post(
            "/api/auth/email-code",
            json={"purpose": "unknown"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_request_email_code_requires_auth(self, client):
        resp = client.post("/api/auth/email-code", json={"purpose": "change_password"})
        assert resp.status_code == 401


class TestSshKeys:
    @pytest.fixture
    def public_key(self):
        """生成一个真实的 ed25519 测试公钥。"""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization

        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        return public_key.decode("ascii")

    @pytest.fixture
    def gitea_available(self, monkeypatch):
        """模拟 Gitea 可用且添加/删除 SSH key 成功。"""

        class FakeResp:
            def __init__(self, status_code, json_data=None):
                self.status_code = status_code
                self._json = json_data

            def json(self):
                return self._json or {}

        def fake_admin_request(method, path, **kwargs):
            if method == "POST" and "/keys" in path:
                return FakeResp(201, {"id": 42})
            if method == "DELETE" and "/keys/" in path:
                return FakeResp(204)
            return FakeResp(200)

        monkeypatch.setattr(
            "app.services.gitea_client.GiteaClient._is_available", lambda: True
        )
        monkeypatch.setattr(
            "app.services.gitea_client.GiteaClient._admin_request", fake_admin_request
        )

    def test_list_ssh_keys_empty(self, client, auth_headers):
        resp = client.get("/api/auth/ssh-keys", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["keys"] == []

    def test_create_ssh_key_success(
        self, client, auth_headers, gitea_available, public_key
    ):
        resp = client.post(
            "/api/auth/ssh-keys",
            json={"title": "MacBook", "public_key": public_key},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["key"]["title"] == "MacBook"
        assert data["key"]["key_type"] == "ssh-ed25519"
        assert data["key"]["fingerprint"].startswith("SHA256:")

    def test_create_ssh_key_duplicate(
        self, client, auth_headers, gitea_available, public_key
    ):
        client.post(
            "/api/auth/ssh-keys",
            json={"title": "MacBook", "public_key": public_key},
            headers=auth_headers,
        )
        resp = client.post(
            "/api/auth/ssh-keys",
            json={"title": "MacBook2", "public_key": public_key},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_ssh_key_invalid_format(self, client, auth_headers, gitea_available):
        resp = client.post(
            "/api/auth/ssh-keys",
            json={"title": "Bad", "public_key": "not-a-key"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_ssh_key_gitea_unavailable(
        self, client, auth_headers, monkeypatch, public_key
    ):
        monkeypatch.setattr(
            "app.services.gitea_client.GiteaClient._is_available", lambda: False
        )
        resp = client.post(
            "/api/auth/ssh-keys",
            json={"title": "MacBook", "public_key": public_key},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()["key"]
        assert data["sync_status"] == "pending"

    def test_delete_ssh_key_success(
        self, client, auth_headers, gitea_available, public_key
    ):
        create_resp = client.post(
            "/api/auth/ssh-keys",
            json={"title": "MacBook", "public_key": public_key},
            headers=auth_headers,
        )
        key_id = create_resp.get_json()["key"]["id"]

        resp = client.delete(f"/api/auth/ssh-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert UserSshKey.query.count() == 0

    def test_delete_ssh_key_not_found(self, client, auth_headers, gitea_available):
        resp = client.delete("/api/auth/ssh-keys/non-existent", headers=auth_headers)
        assert resp.status_code == 404

    def test_validate_public_key(self, public_key):
        key_type, key_data, fingerprint = SshKeyService.validate_public_key(public_key)
        assert key_type == "ssh-ed25519"
        assert fingerprint.startswith("SHA256:")
