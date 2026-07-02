"""徽章管理面板：定义 CRUD + 发放/撤销 + 权限。"""

import pytest

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
    """将指定用户提权为 admin。"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        user.role = "admin"
        db.session.commit()
        return user.id


def _get_user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


class TestBadgeCRUD:
    def test_admin_can_create_badge(self, client, app, auth_headers):
        """admin 可创建徽章。"""
        _login(client, "admin1", "admin1@example.com")
        _promote_admin(app, "admin1")
        admin_headers = _login(client, "admin1", "admin1@example.com")

        r = client.post("/api/admin/badges", json={
            "name": "测试徽章",
            "description": "用于测试",
            "icon": "🏆",
            "color": "#5e6ad2",
        }, headers=admin_headers)
        assert r.status_code == 201, r.get_json()
        data = r.get_json()["badge"]
        assert data["name"] == "测试徽章"
        assert data["slug"]
        assert data["kind"] == "custom"
        assert data["color"] == "#5e6ad2"

    def test_non_admin_cannot_create(self, client, auth_headers):
        """普通用户创建 -> 403。"""
        r = client.post("/api/admin/badges", json={
            "name": "禁止徽章",
        }, headers=auth_headers)
        assert r.status_code == 403

    def test_unauthenticated_cannot_create(self, client):
        """未登录创建 -> 401。"""
        r = client.post("/api/admin/badges", json={"name": "x"})
        assert r.status_code == 401

    def test_duplicate_name_conflict(self, client, app):
        _login(client, "admin2", "admin2@example.com")
        _promote_admin(app, "admin2")
        h = _login(client, "admin2", "admin2@example.com")

        client.post("/api/admin/badges", json={"name": "唯一徽章"}, headers=h)
        r = client.post("/api/admin/badges", json={"name": "唯一徽章"}, headers=h)
        assert r.status_code == 409

    def test_list_and_get_public(self, client, app):
        _login(client, "admin3", "admin3@example.com")
        _promote_admin(app, "admin3")
        h = _login(client, "admin3", "admin3@example.com")

        client.post("/api/admin/badges", json={"name": "公开徽章", "color": "#0eb478"}, headers=h)

        # 公开列表
        r = client.get("/api/badges")
        assert r.status_code == 200
        names = [b["name"] for b in r.get_json()["badges"]]
        assert "公开徽章" in names

        slug = r.get_json()["badges"][0]["slug"]
        # 公开单个
        r2 = client.get(f"/api/badges/{slug}")
        assert r2.status_code == 200
        assert r2.get_json()["badge"]["slug"] == slug

    def test_update_badge(self, client, app):
        _login(client, "admin4", "admin4@example.com")
        _promote_admin(app, "admin4")
        h = _login(client, "admin4", "admin4@example.com")

        created = client.post("/api/admin/badges", json={"name": "旧名"}, headers=h).get_json()["badge"]
        r = client.patch(f"/api/admin/badges/{created['id']}", json={
            "description": "新描述", "color": "#f5a623",
        }, headers=h)
        assert r.status_code == 200
        data = r.get_json()["badge"]
        assert data["description"] == "新描述"
        assert data["color"] == "#f5a623"

    def test_delete_badge(self, client, app):
        _login(client, "admin5", "admin5@example.com")
        _promote_admin(app, "admin5")
        h = _login(client, "admin5", "admin5@example.com")

        created = client.post("/api/admin/badges", json={"name": "待删"}, headers=h).get_json()["badge"]
        r = client.delete(f"/api/admin/badges/{created['id']}", headers=h)
        assert r.status_code == 200
        # 再次获取应 404
        r2 = client.get(f"/api/badges/{created['slug']}")
        assert r2.status_code == 404

    def test_update_nonexistent_404(self, client, app):
        _login(client, "admin6", "admin6@example.com")
        _promote_admin(app, "admin6")
        h = _login(client, "admin6", "admin6@example.com")
        r = client.patch("/api/admin/badges/nonexistent-id", json={"name": "x"}, headers=h)
        assert r.status_code == 404


class TestAwardRevoke:
    def _setup_admin_and_badge(self, client, app):
        _login(client, "boss", "boss@example.com")
        admin_id = _promote_admin(app, "boss")
        h = _login(client, "boss", "boss@example.com")
        badge = client.post("/api/admin/badges", json={
            "name": "贡献者", "icon": "🎖",
        }, headers=h).get_json()["badge"]
        # 被发放用户
        _login(client, "target", "target@example.com")
        target_id = _get_user_id(app, "target")
        return h, badge, target_id

    def test_award_success(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        r = client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id, "reason": "感谢贡献",
        }, headers=h)
        assert r.status_code == 201, r.get_json()
        award = r.get_json()["award"]
        assert award["user_id"] == target_id
        assert award["badge_id"] == badge["id"]
        assert award["reason"] == "感谢贡献"

    def test_award_duplicate_conflict(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        r = client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        assert r.status_code == 409

    def test_revoke_success(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        r = client.delete(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        assert r.status_code == 200

        # 查获得者列表应为空
        rec = client.get(f"/api/admin/badges/{badge['id']}/recipients", headers=h).get_json()
        assert rec["recipients"] == []

    def test_revoke_nonexistent_404(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        # 未发放就撤销
        r = client.delete(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        assert r.status_code == 404

    def test_recipients_list(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        r = client.get(f"/api/admin/badges/{badge['id']}/recipients", headers=h)
        assert r.status_code == 200
        recs = r.get_json()["recipients"]
        assert len(recs) == 1
        assert recs[0]["user_id"] == target_id

    def test_non_admin_cannot_award(self, client, app, auth_headers):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        # auth_headers 是 testuser（普通用户）
        r = client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=auth_headers)
        assert r.status_code == 403

    def test_user_badges_endpoint(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        # 公开查询 target 的徽章
        r = client.get("/api/users/target/badges")
        assert r.status_code == 200
        badges = r.get_json()["badges"]
        assert len(badges) == 1
        assert badges[0]["badge"]["name"] == "贡献者"

    def test_profile_includes_awarded_badges(self, client, app):
        h, badge, target_id = self._setup_admin_and_badge(client, app)
        client.post(f"/api/admin/badges/{badge['id']}/award", json={
            "user_id": target_id,
        }, headers=h)
        r = client.get("/api/users/target")
        assert r.status_code == 200
        awarded = r.get_json()["awarded_badges"]
        assert len(awarded) == 1
