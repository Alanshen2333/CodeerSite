"""Test Issue 评论流：多态 comment target_type=issue。"""

import pytest


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Issue Comment Project"):
    r = client.post("/api/projects", json={"name": name, "visibility": "public"}, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["project"]


def _create_issue(client, headers, slug, title="Test Issue"):
    r = client.post(f"/api/projects/{slug}/issues", json={
        "title": title, "body": "body", "priority": "medium",
    }, headers=headers)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["issue"]


class TestIssueComment:
    def test_create_and_list_issue_comment(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])

        r = client.post("/api/comments", json={
            "body": "first comment", "target_type": "issue", "target_id": issue["id"],
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.get_json()["comment"]["body"] == "first comment"

        r = client.get("/api/comments", query_string={
            "target_type": "issue", "target_id": issue["id"],
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] == 1
        assert data["comments"][0]["body"] == "first comment"

    def test_issue_target_now_accepted(self, client, auth_headers):
        """回归保护：schema OneOf 已含 issue（曾经会 422）。"""
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post("/api/comments", json={
            "body": "x", "target_type": "issue", "target_id": issue["id"],
        }, headers=auth_headers)
        assert r.status_code == 201

    def test_comment_requires_auth(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post("/api/comments", json={
            "body": "x", "target_type": "issue", "target_id": issue["id"],
        })
        assert r.status_code == 401

    def test_delete_own_comment(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post("/api/comments", json={
            "body": "mine", "target_type": "issue", "target_id": issue["id"],
        }, headers=auth_headers)
        cid = r.get_json()["comment"]["id"]

        r = client.delete(f"/api/comments/{cid}", headers=auth_headers)
        assert r.status_code == 200

        r = client.get("/api/comments", query_string={
            "target_type": "issue", "target_id": issue["id"],
        })
        assert r.get_json()["total"] == 0

    def test_delete_others_comment_forbidden(self, client, auth_headers):
        p = _create_project(client, auth_headers)
        issue = _create_issue(client, auth_headers, p["slug"])
        r = client.post("/api/comments", json={
            "body": "owner's", "target_type": "issue", "target_id": issue["id"],
        }, headers=auth_headers)
        cid = r.get_json()["comment"]["id"]

        h_other = _login(client, "otheruser", "other@example.com")
        r = client.delete(f"/api/comments/{cid}", headers=h_other)
        assert r.status_code == 403
