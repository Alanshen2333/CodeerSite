"""Issue #16: 邮箱验证码重发冷却。"""

from datetime import datetime, timezone, timedelta

import pytest

from app.extensions import db
from app.models.email_verification_code import EmailVerificationCode


@pytest.mark.usefixtures("auth_headers")
class TestEmailCodeCooldown:
    def test_first_send_succeeds(self, client, auth_headers):
        """首次发送验证码 -> 200。"""
        resp = client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_cooldown_blocks_resend(self, client, auth_headers):
        """冷却期内重发 -> 429。"""
        client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )

        resp = client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 429

    def test_cooldown_expiry_allows_resend(self, client, auth_headers, app):
        """冷却期过后可重发。"""
        client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )

        # Manually advance sent_at past cooldown
        with app.app_context():
            record = EmailVerificationCode.query.filter_by(
                email="test@example.com", purpose="change_password"
            ).one()
            record.sent_at = datetime.now(timezone.utc) - timedelta(seconds=61)
            db.session.commit()

        resp = client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_different_purposes_independent(self, client, auth_headers):
        """不同 purpose 的冷却互相独立。"""
        # Send change_password code
        client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )

        # Send disable_2fa code immediately - should succeed
        resp = client.post(
            "/api/auth/email-code",
            json={
                "purpose": "disable_2fa",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # But resend change_password should still be blocked
        resp = client.post(
            "/api/auth/email-code",
            json={
                "purpose": "change_password",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 429
