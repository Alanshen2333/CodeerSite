"""Issue #29: 邮箱验证码迁移到 PostgreSQL 后的持久化与一次性消费。"""

from app.extensions import db
from app.services.email_code_service import EmailCodeService


class TestPostgresEmailCode:
    def test_code_persists_across_session_removal(
        self, app, client, auth_headers
    ):
        """验证码写入 PG，而不是进程内存：移除 session 后仍可验证。"""
        with app.app_context():
            code = EmailCodeService.send_code("test@example.com", "change_password")
            db.session.remove()

        resp = client.post(
            "/api/auth/change-password",
            json={
                "verification_code": code,
                "new_password": "newpassword123",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_verify_code_is_one_time(self, app, auth_headers):
        with app.app_context():
            code = EmailCodeService.send_code("test@example.com", "change_password")
            assert EmailCodeService.verify_code(
                "test@example.com", "change_password", code
            ) is True
            assert EmailCodeService.verify_code(
                "test@example.com", "change_password", code
            ) is False

    def test_wrong_code_does_not_consume_valid_code(self, app, auth_headers):
        with app.app_context():
            code = EmailCodeService.send_code("test@example.com", "change_password")
            assert EmailCodeService.verify_code(
                "test@example.com", "change_password", "000000"
            ) is False
            assert EmailCodeService.verify_code(
                "test@example.com", "change_password", code
            ) is True
