"""Issue #23: Milestone open/closed_issues 计数缓存，消除 N+1。"""

import pytest

from app.extensions import db
from app.models.milestone import Milestone
from app.models.issue import Issue
from app.services.milestone_service import MilestoneService


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Test Project"):
    resp = client.post("/api/projects", json={"name": name, "visibility": "public"}, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["project"]


def _create_milestone(client, headers, slug, title="Sprint 1"):
    resp = client.post(f"/api/projects/{slug}/milestones", json={"title": title}, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["milestone"]


def _create_issue(client, headers, slug, title, milestone_id=None):
    payload = {"title": title}
    if milestone_id:
        payload["milestone_id"] = milestone_id
    resp = client.post(f"/api/projects/{slug}/issues", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["issue"]


@pytest.mark.usefixtures("auth_headers")
class TestMilestoneCounts:
    def test_counts_after_create(self, client, app, auth_headers):
        """创建 issue 后 milestone 计数正确。"""
        p = _create_project(client, auth_headers)
        m = _create_milestone(client, auth_headers, p["slug"])
        _create_issue(client, auth_headers, p["slug"], "Task 1", m["id"])
        _create_issue(client, auth_headers, p["slug"], "Task 2", m["id"])

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        ms = resp.get_json()["milestones"][0]
        assert ms["open_issues"] == 2
        assert ms["closed_issues"] == 0

    def test_counts_after_status_change(self, client, app, auth_headers):
        """关闭 issue 后计数正确更新。"""
        p = _create_project(client, auth_headers)
        m = _create_milestone(client, auth_headers, p["slug"])
        issue = _create_issue(client, auth_headers, p["slug"], "Task", m["id"])

        # Close the issue
        resp = client.patch(
            f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
            json={"status": "closed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        ms = resp.get_json()["milestones"][0]
        assert ms["open_issues"] == 0
        assert ms["closed_issues"] == 1

    def test_counts_after_reopen(self, client, app, auth_headers):
        """关闭后再打开 issue，计数回滚正确。"""
        p = _create_project(client, auth_headers)
        m = _create_milestone(client, auth_headers, p["slug"])
        issue = _create_issue(client, auth_headers, p["slug"], "Task", m["id"])

        # Close then reopen
        client.patch(f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
                     json={"status": "closed"}, headers=auth_headers)
        client.patch(f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
                     json={"status": "open"}, headers=auth_headers)

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        ms = resp.get_json()["milestones"][0]
        assert ms["open_issues"] == 1
        assert ms["closed_issues"] == 0

    def test_counts_after_milestone_change(self, client, app, auth_headers):
        """issue 换 milestone 后旧/新计数正确。"""
        p = _create_project(client, auth_headers)
        m1 = _create_milestone(client, auth_headers, p["slug"], "Sprint 1")
        m2 = _create_milestone(client, auth_headers, p["slug"], "Sprint 2")
        issue = _create_issue(client, auth_headers, p["slug"], "Task", m1["id"])

        # Move to m2
        client.patch(f"/api/projects/{p['slug']}/issues/{issue['issue_number']}",
                     json={"milestone_id": m2["id"]}, headers=auth_headers)

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        milestones = {m["id"]: m for m in resp.get_json()["milestones"]}
        assert milestones[m1["id"]]["open_issues"] == 0
        assert milestones[m2["id"]]["open_issues"] == 1

    def test_counts_after_delete(self, client, app, auth_headers):
        """删除 issue 后计数减少。"""
        p = _create_project(client, auth_headers)
        m = _create_milestone(client, auth_headers, p["slug"])
        issue = _create_issue(client, auth_headers, p["slug"], "Task", m["id"])

        client.delete(f"/api/projects/{p['slug']}/issues/{issue['issue_number']}", headers=auth_headers)

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        ms = resp.get_json()["milestones"][0]
        assert ms["open_issues"] == 0

    def test_no_n_plus1(self, client, app, auth_headers):
        """多个 milestone 列表不触发 N+1（to_dict 使用缓存值）。"""
        p = _create_project(client, auth_headers)
        m1 = _create_milestone(client, auth_headers, p["slug"], "S1")
        m2 = _create_milestone(client, auth_headers, p["slug"], "S2")
        m3 = _create_milestone(client, auth_headers, p["slug"], "S3")
        _create_issue(client, auth_headers, p["slug"], "T1", m1["id"])
        _create_issue(client, auth_headers, p["slug"], "T2", m1["id"])
        _create_issue(client, auth_headers, p["slug"], "T3", m2["id"])

        resp = client.get(f"/api/projects/{p['slug']}/milestones")
        milestones = {m["title"]: m for m in resp.get_json()["milestones"]}
        assert milestones["S1"]["open_issues"] == 2
        assert milestones["S2"]["open_issues"] == 1
        assert milestones["S3"]["open_issues"] == 0
