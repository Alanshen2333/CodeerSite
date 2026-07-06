import io
import pytest
from PIL import Image
from app.extensions import db
from app.models.user import User
from app.services.email_code_service import EmailCodeService


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
        EmailCodeService.send_code("test@example.com", "change_password")
        code = EmailCodeService._memory_store[
            EmailCodeService._key("test@example.com", "change_password")
        ]["code"]

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
