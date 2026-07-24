"""Test 加成员：用户搜索 + add_member 去重 + 权限。"""



def _login(client, username, email):
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Member Test Project"):
    resp = client.post(
        "/api/projects",
        json={"name": name, "visibility": "public"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["project"]


def _find_user(client, headers, username):
    r = client.get("/api/users", query_string={"q": username}, headers=headers)
    assert r.status_code == 200
    return next(u for u in r.get_json()["users"] if u["username"] == username)


class TestAddMember:
    def test_search_users_by_username(self, client, auth_headers):
        _login(client, "alice", "alice@example.com")
        r = client.get("/api/users", query_string={"q": "alice"}, headers=auth_headers)
        assert r.status_code == 200
        assert any(u["username"] == "alice" for u in r.get_json()["users"])

    def test_search_users_by_display_name(self, client, auth_headers):
        client.post(
            "/api/auth/register",
            json={
                "username": "dnameuser",
                "email": "dn@example.com",
                "password": "password123",
            },
        )
        # 设 display_name
        client.patch(
            "/api/auth/me", json={"display_name": "ZoeUnique"}, headers=auth_headers
        )
        r = client.get(
            "/api/users", query_string={"q": "ZoeUnique"}, headers=auth_headers
        )
        # 当前测试用户 display_name 设为 ZoeUnique，应能搜到
        assert any(u.get("display_name") == "ZoeUnique" for u in r.get_json()["users"])

    def test_add_member_and_list(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        _login(client, "bob", "bob@example.com")
        bob = _find_user(client, auth_headers, "bob")

        r = client.post(
            f"/api/projects/{slug}/members",
            json={
                "user_id": bob["id"],
                "role": "member",
            },
            headers=auth_headers,
        )
        assert r.status_code == 201

        members = client.get(
            f"/api/projects/{slug}/members", headers=auth_headers
        ).get_json()["members"]
        assert bob["id"] in [m["user_id"] for m in members]

    def test_add_member_dedup_conflict(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        slug = p["slug"]
        _login(client, "carol", "carol@example.com")
        carol = _find_user(client, auth_headers, "carol")

        client.post(
            f"/api/projects/{slug}/members",
            json={
                "user_id": carol["id"],
                "role": "member",
            },
            headers=auth_headers,
        )

        # 重复添加 -> 409 Conflict
        r = client.post(
            f"/api/projects/{slug}/members",
            json={
                "user_id": carol["id"],
            },
            headers=auth_headers,
        )
        assert r.status_code == 409

    def test_non_member_cannot_add(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        h_outsider = _login(client, "outsider", "out@example.com")
        outsider = _find_user(client, auth_headers, "outsider")

        # outsider 不是该项目成员/管理员，无权加人 -> 403
        r = client.post(
            f"/api/projects/{p['slug']}/members",
            json={
                "user_id": outsider["id"],
            },
            headers=h_outsider,
        )
        assert r.status_code == 403
