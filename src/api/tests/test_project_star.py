"""Test 项目 Star 真实化：toggle / 去重 / star_count 同步 / starred 标注 / 匿名态。"""

import pytest


def _create_project(client, headers, name="Starred Project"):
    resp = client.post(
        "/api/projects",
        json={"name": name, "visibility": "public"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["project"]


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


@pytest.mark.usefixtures("auth_headers")
class TestProjectStar:
    def test_star_toggle_and_dedup(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]

        # star -> starred=True, count=1
        r = client.post(f"/api/projects/{slug}/star", headers=auth_headers)
        assert r.status_code == 200
        assert r.get_json() == {"starred": True, "star_count": 1}

        # 再 star -> toggle 取消（去重，靠唯一约束），count=0
        r = client.post(f"/api/projects/{slug}/star", headers=auth_headers)
        assert r.get_json() == {"starred": False, "star_count": 0}

    def test_star_requires_auth(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        r = client.post(f"/api/projects/{p['slug']}/star")
        assert r.status_code == 401

    def test_star_count_accumulates_across_users(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        h2 = _login(client, "user2", "u2@example.com")

        client.post(f"/api/projects/{slug}/star", headers=auth_headers)
        client.post(f"/api/projects/{slug}/star", headers=h2)

        r = client.get(f"/api/projects/{slug}", headers=auth_headers)
        proj = r.get_json()["project"]
        assert proj["star_count"] == 2
        assert proj["starred"] is True  # 第一用户已 star

    def test_starred_false_for_anonymous(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]

        # 匿名访问：starred=False, count=0
        proj = client.get(f"/api/projects/{slug}").get_json()["project"]
        assert proj["starred"] is False
        assert proj["star_count"] == 0

        # 登录后 star，匿名再访问：count=1 但 starred 仍 False（匿名无身份）
        client.post(f"/api/projects/{slug}/star", headers=auth_headers)
        proj = client.get(f"/api/projects/{slug}").get_json()["project"]
        assert proj["starred"] is False
        assert proj["star_count"] == 1

    def test_starred_flag_in_list(self, client, auth_headers):
        p = _create_project(client, auth_headers, name="List Star Test")
        client.post(f"/api/projects/{p['slug']}/star", headers=auth_headers)

        projs = client.get("/api/projects", headers=auth_headers).get_json()["projects"]
        target = next(x for x in projs if x["slug"] == p["slug"])
        assert target["starred"] is True
        assert target["star_count"] == 1
