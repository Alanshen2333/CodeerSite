"""Issue #29: 通知迁移到 PostgreSQL 后保持 API 响应兼容。"""

from app.services.notification_service import NotificationService


class TestNotifications:
    def _create_notifications(self, client, auth_headers, app):
        me = client.get("/api/auth/me", headers=auth_headers).get_json()
        user_id = me["user"]["id"]
        with app.app_context():
            NotificationService.create(
                recipient_id=user_id,
                type_="test",
                title="first",
                body="body-first",
                link="/first",
            )
            NotificationService.create(
                recipient_id=user_id,
                type_="test",
                title="second",
                body="body-second",
                link="/second",
            )
        return user_id

    def test_list_unread_and_mark_read(self, client, auth_headers, app):
        self._create_notifications(client, auth_headers, app)

        resp = client.get("/api/notifications", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["pages"] == 1
        assert len(data["items"]) == 2
        first = data["items"][0]
        assert first["title"] == "second"
        assert first["is_read"] is False
        assert first["created_at"] is not None

        unread = client.get("/api/notifications/unread-count", headers=auth_headers)
        assert unread.status_code == 200
        assert unread.get_json()["unread_count"] == 2

        read_resp = client.patch(
            f"/api/notifications/{first['id']}/read", headers=auth_headers
        )
        assert read_resp.status_code == 200

        unread = client.get("/api/notifications/unread-count", headers=auth_headers)
        assert unread.get_json()["unread_count"] == 1

    def test_mark_all_read(self, client, auth_headers, app):
        self._create_notifications(client, auth_headers, app)

        resp = client.patch("/api/notifications/read-all", headers=auth_headers)
        assert resp.status_code == 200

        unread = client.get("/api/notifications/unread-count", headers=auth_headers)
        assert unread.get_json()["unread_count"] == 0

    def test_mark_read_other_user_not_found(self, client, auth_headers, app):
        self._create_notifications(client, auth_headers, app)

        # 第二个用户尝试读不属于自己的通知：单条已读应 404
        client.post(
            "/api/auth/register",
            json={
                "username": "otheruser",
                "email": "other@example.com",
                "password": "password123",
            },
        )
        other_login = client.post(
            "/api/auth/login",
            json={"email": "other@example.com", "password": "password123"},
        ).get_json()
        other_headers = {
            "Authorization": f"Bearer {other_login['access_token']}"
        }

        # 拿一条真实通知 id
        notes = client.get("/api/notifications", headers=auth_headers).get_json()
        assert notes["items"]
        notification_id = notes["items"][0]["id"]

        resp = client.patch(
            f"/api/notifications/{notification_id}/read", headers=other_headers
        )
        assert resp.status_code == 404
