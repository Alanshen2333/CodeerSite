"""Test Issue 时间跟踪：预估工时设置、耗时条目记录与聚合、权限。"""



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


def _create_project(client, headers, name="Time Tracking Project"):
    r = client.post(
        "/api/projects", json={"name": name, "visibility": "public"}, headers=headers
    )
    assert r.status_code == 201, r.get_json()
    return r.get_json()["project"]


def _create_issue(client, headers, slug, title="Test Issue", **extra):
    payload = {"title": title, "body": "body", "priority": "medium"}
    payload.update(extra)
    r = client.post(f"/api/projects/{slug}/issues", json=payload, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["issue"]


class TestIssueTimeTracking:
    def test_set_time_estimate_on_create(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        # 30 分钟 = 1800 秒
        issue = _create_issue(client, auth_headers, p["slug"], time_estimate=1800)
        assert issue["time_estimate"] == 1800
        assert issue["time_spent"] == 0

    def test_update_time_estimate(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"], time_estimate=1800)

        r = client.patch(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            json={"time_estimate": 3600},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.get_json()["issue"]["time_estimate"] == 3600

    def test_clear_time_estimate(self, client, auth_headers):
        """allow_none 字段：显式 null 应清空估时。"""
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"], time_estimate=1800)

        r = client.patch(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            json={"time_estimate": None},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.get_json()["issue"]["time_estimate"] is None

    def test_negative_estimate_rejected(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        r = client.post(
            f"/api/projects/{p['slug']}/issues",
            json={
                "title": "x",
                "time_estimate": -1,
            },
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_time_entry_aggregates(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        r = client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 1500, "note": "first"},
            headers=auth_headers,
        )
        assert r.status_code == 201, r.get_json()
        data = r.get_json()
        assert data["entry"]["seconds"] == 1500
        assert data["entry"]["note"] == "first"
        # time_spent 反范式缓存已累加
        assert data["issue"]["time_spent"] == 1500

    def test_multiple_entries_accumulate(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 1500},
            headers=auth_headers,
        )
        client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 900},
            headers=auth_headers,
        )
        r = client.get(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            headers=auth_headers,
        )
        assert r.get_json()["issue"]["time_spent"] == 2400

    def test_list_time_entries(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 600, "note": "a"},
            headers=auth_headers,
        )
        client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 300, "note": "b"},
            headers=auth_headers,
        )
        r = client.get(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] == 2
        # 倒序：最新在前
        assert data["time_entries"][0]["note"] == "b"

    def test_time_entry_requires_auth(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 60},
        )
        assert r.status_code == 401

    def test_time_entry_non_member_forbidden(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        h_other = _login(client, "outsider", "out@example.com")
        r = client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 60},
            headers=h_other,
        )
        assert r.status_code == 403

    def test_list_time_entries_non_member_forbidden(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        h_other = _login(client, "outsider2", "out2@example.com")
        r = client.get(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            headers=h_other,
        )
        assert r.status_code == 403

    def test_zero_seconds_rejected(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}/time-entries",
            json={"seconds": 0},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_time_entry_on_missing_issue(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        r = client.post(
            f"/api/projects/{p['slug']}/issues/9999/time-entries",
            json={"seconds": 60},
            headers=auth_headers,
        )
        assert r.status_code == 404
