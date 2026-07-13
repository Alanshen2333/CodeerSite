"""Issue #17: update_me 字段白名单 + admin 用户更新 Schema 校验。"""

from app.extensions import db
from app.models.user import User


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _promote_admin(app, username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        user.role = "admin"
        db.session.commit()
        return user.id


def _get_user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


class TestUpdateMeWhitelist:
    """update_me 只允许修改白名单字段，拒绝 role / is_active 等敏感字段。"""

    def test_cannot_set_role(self, client, auth_headers):
        """尝试通过 update_me 设置 role -> 422。"""
        resp = client.patch("/api/auth/me", json={
            "role": "admin",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_cannot_set_is_active(self, client, auth_headers):
        """尝试通过 update_me 设置 is_active -> 422。"""
        resp = client.patch("/api/auth/me", json={
            "is_active": False,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_normal_fields_still_work(self, client, auth_headers):
        """正常字段仍可修改。"""
        resp = client.patch("/api/auth/me", json={
            "display_name": "新名字",
            "bio": "新简介",
            "website": "https://example.com",
            "location": "上海",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()["user"]
        assert data["display_name"] == "新名字"
        assert data["bio"] == "新简介"
        assert data["website"] == "https://example.com"
        assert data["location"] == "上海"

    def test_role_not_escalated(self, client, app, auth_headers):
        """即使绕过前端直接发 role，数据库中 role 不变。"""
        client.patch("/api/auth/me", json={
            "role": "admin",
        }, headers=auth_headers)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            assert user.role == "user"


class TestAdminUserUpdate:
    """admin 更新用户接口通过 Schema 校验。"""

    def test_update_role_valid(self, client, app, auth_headers):
        """admin 可修改用户 role。"""
        _login(client, "targetuser", "target@example.com")
        target_id = _get_user_id(app, "targetuser")

        _login(client, "adminuser", "admin@example.com")
        _promote_admin(app, "adminuser")
        admin_headers = _login(client, "adminuser", "admin@example.com")

        resp = client.patch(f"/api/admin/users/{target_id}", json={
            "role": "moderator",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["user"]["role"] == "moderator"

    def test_update_role_invalid(self, client, app, auth_headers):
        """无效 role 值 -> 422。"""
        _login(client, "targetuser2", "target2@example.com")
        target_id = _get_user_id(app, "targetuser2")

        _login(client, "adminuser2", "admin2@example.com")
        _promote_admin(app, "adminuser2")
        admin_headers = _login(client, "adminuser2", "admin2@example.com")

        resp = client.patch(f"/api/admin/users/{target_id}", json={
            "role": "superadmin",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_update_is_active(self, client, app, auth_headers):
        """admin 可停用用户。"""
        _login(client, "targetuser3", "target3@example.com")
        target_id = _get_user_id(app, "targetuser3")

        _login(client, "adminuser3", "admin3@example.com")
        _promote_admin(app, "adminuser3")
        admin_headers = _login(client, "adminuser3", "admin3@example.com")

        resp = client.patch(f"/api/admin/users/{target_id}", json={
            "is_active": False,
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["user"]["is_active"] is False

    def test_non_admin_cannot_update(self, client, app, auth_headers):
        """普通用户无权访问 -> 403。"""
        _login(client, "targetuser4", "target4@example.com")
        target_id = _get_user_id(app, "targetuser4")

        resp = client.patch(f"/api/admin/users/{target_id}", json={
            "role": "admin",
        }, headers=auth_headers)
        assert resp.status_code == 403

    def test_rejects_unknown_field(self, client, app, auth_headers):
        """未知字段 -> 422。"""
        _login(client, "targetuser5", "target5@example.com")
        target_id = _get_user_id(app, "targetuser5")

        _login(client, "adminuser5", "admin5@example.com")
        _promote_admin(app, "adminuser5")
        admin_headers = _login(client, "adminuser5", "admin5@example.com")

        resp = client.patch(f"/api/admin/users/{target_id}", json={
            "password_hash": "malicious",
        }, headers=admin_headers)
        assert resp.status_code == 422
