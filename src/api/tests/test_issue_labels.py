"""Test Issue 标签：复用全局 tag 多对多关联 + 更新 + 列表筛选。"""


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Label Project"):
    r = client.post("/api/projects", json={"name": name, "visibility": "public"}, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["project"]


def _create_tag(client, headers, name):
    r = client.post("/api/tags", json={"name": name}, headers=headers)
    assert r.status_code in (200, 201), r.get_json()
    return r.get_json()["tag"]


def _create_issue(client, headers, slug, title="Labeled Issue", tag_ids=None):
    body = {"title": title, "body": "b", "priority": "medium"}
    if tag_ids is not None:
        body["tag_ids"] = tag_ids
    r = client.post(f"/api/projects/{slug}/issues", json=body, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["issue"]


class TestIssueLabels:
    def test_create_issue_with_tags(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        t1 = _create_tag(client, auth_headers, "bug-label")
        t2 = _create_tag(client, auth_headers, "ui-label")
        issue = _create_issue(client, auth_headers, p["slug"], tag_ids=[t1["id"], t2["id"]])
        assert {t["id"] for t in issue["tags"]} == {t1["id"], t2["id"]}

    def test_get_issue_returns_tags(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        t = _create_tag(client, auth_headers, "feature")
        issue = _create_issue(client, auth_headers, p["slug"], tag_ids=[t["id"]])
        r = client.get(f"/api/projects/{p['slug']}/issues/{issue['issue_number']}")
        assert r.status_code == 200
        assert r.get_json()["issue"]["tags"][0]["name"] == "feature"

    def test_update_tags_replace_and_clear(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        t1 = _create_tag(client, auth_headers, "alpha")
        t2 = _create_tag(client, auth_headers, "beta")
        issue = _create_issue(client, auth_headers, p["slug"], tag_ids=[t1["id"]])

        # 替换为 t2
        r = client.patch(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            json={"tag_ids": [t2["id"]]}, headers=auth_headers,
        )
        assert r.status_code == 200
        assert [t["id"] for t in r.get_json()["issue"]["tags"]] == [t2["id"]]

        # 清空
        r = client.patch(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            json={"tag_ids": []}, headers=auth_headers,
        )
        assert r.get_json()["issue"]["tags"] == []

    def test_list_filter_by_tag(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        t = _create_tag(client, auth_headers, "filtertag")
        _create_issue(client, auth_headers, p["slug"], title="With tag", tag_ids=[t["id"]])
        _create_issue(client, auth_headers, p["slug"], title="No tag")

        r = client.get(f"/api/projects/{p['slug']}/issues", query_string={"tag_id": t["id"]})
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] == 1
        assert data["issues"][0]["title"] == "With tag"
