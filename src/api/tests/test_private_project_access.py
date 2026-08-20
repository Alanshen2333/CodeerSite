"""私有项目访问矩阵：匿名/非成员不可见，成员可见。"""

from app.models.project import Project
from app.models.user import User
from app.services.project_service import ProjectService


def _login(client, username: str, email: str) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def _create_private_fixture(client):
    owner_headers = _login(client, "privateowner", "private-owner@example.com")
    member_headers = _login(client, "privatemember", "private-member@example.com")
    outsider_headers = _login(client, "privateoutsider", "private-outsider@example.com")

    response = client.post(
        "/api/projects",
        json={
            "name": "Confidential Project",
            "description": "private-project-secret",
            "visibility": "private",
        },
        headers=owner_headers,
    )
    project_data = response.get_json()["project"]
    project = Project.query.filter_by(slug=project_data["slug"]).first()
    member = User.query.filter_by(username="privatemember").first()
    ProjectService.add_member(project.id, member.id)

    issue_response = client.post(
        f"/api/projects/{project.slug}/issues",
        json={"title": "Private Issue", "body": "private-issue-secret"},
        headers=owner_headers,
    )
    issue = issue_response.get_json()["issue"]

    client.post(
        f"/api/projects/{project.slug}/milestones",
        json={"title": "Private Milestone", "description": "milestone-secret"},
        headers=owner_headers,
    )
    column_response = client.post(
        f"/api/projects/{project.slug}/kanban/columns",
        json={"title": "Private Column"},
        headers=owner_headers,
    )
    client.post(
        f"/api/projects/{project.slug}/kanban/columns/"
        f"{column_response.get_json()['column']['id']}/cards",
        json={"title": "Private Card", "issue_id": issue["id"]},
        headers=owner_headers,
    )
    client.post(
        "/api/comments",
        json={
            "target_type": "issue",
            "target_id": issue["id"],
            "body": "private-comment-secret",
        },
        headers=owner_headers,
    )

    return {
        "slug": project.slug,
        "issue": issue,
        "owner_headers": owner_headers,
        "member_headers": member_headers,
        "outsider_headers": outsider_headers,
    }


def _assert_private_resources_hidden(client, fixture, headers=None):
    slug = fixture["slug"]
    issue = fixture["issue"]
    requests = [
        (f"/api/projects/{slug}", None),
        (f"/api/projects/{slug}/members", None),
        (f"/api/projects/{slug}/issues", None),
        (f"/api/projects/{slug}/issues/{issue['issue_number']}", None),
        (f"/api/projects/{slug}/milestones", None),
        (f"/api/projects/{slug}/kanban/columns", None),
        (
            "/api/comments",
            {"target_type": "issue", "target_id": issue["id"]},
        ),
    ]
    for path, query_string in requests:
        response = client.get(path, query_string=query_string, headers=headers)
        assert response.status_code == 404, (path, response.get_json())


class TestPrivateProjectReadAccess:
    def test_anonymous_cannot_enumerate_or_read(self, client):
        fixture = _create_private_fixture(client)

        projects = client.get("/api/projects").get_json()["projects"]
        assert fixture["slug"] not in {project["slug"] for project in projects}
        _assert_private_resources_hidden(client, fixture)

    def test_non_member_cannot_enumerate_or_read(self, client):
        fixture = _create_private_fixture(client)

        projects = client.get(
            "/api/projects", headers=fixture["outsider_headers"]
        ).get_json()["projects"]
        assert fixture["slug"] not in {project["slug"] for project in projects}
        _assert_private_resources_hidden(client, fixture, fixture["outsider_headers"])

    def test_member_can_enumerate_and_read(self, client):
        fixture = _create_private_fixture(client)
        headers = fixture["member_headers"]
        slug = fixture["slug"]

        projects = client.get("/api/projects", headers=headers).get_json()["projects"]
        assert slug in {project["slug"] for project in projects}
        assert client.get(f"/api/projects/{slug}", headers=headers).status_code == 200
        assert (
            client.get(f"/api/projects/{slug}/issues", headers=headers).status_code
            == 200
        )
        assert (
            client.get(
                "/api/comments",
                query_string={
                    "target_type": "issue",
                    "target_id": fixture["issue"]["id"],
                },
                headers=headers,
            ).status_code
            == 200
        )

    def test_private_project_and_issue_are_filtered_from_search(self, client):
        fixture = _create_private_fixture(client)

        for headers in (None, fixture["outsider_headers"]):
            project_results = client.get(
                "/api/search",
                query_string={"q": "private-project-secret"},
                headers=headers,
            ).get_json()["items"]
            issue_results = client.get(
                "/api/search",
                query_string={"q": "private-issue-secret"},
                headers=headers,
            ).get_json()["items"]
            assert project_results == []
            assert issue_results == []

        member_results = client.get(
            "/api/search",
            query_string={"q": "private-issue-secret"},
            headers=fixture["member_headers"],
        ).get_json()["items"]
        assert any(item["source_type"] == "issue" for item in member_results)

    def test_public_project_remains_anonymously_readable(self, client):
        owner_headers = _login(client, "publicowner", "public-owner@example.com")
        project = client.post(
            "/api/projects",
            json={"name": "Public Project", "visibility": "public"},
            headers=owner_headers,
        ).get_json()["project"]

        assert client.get(f"/api/projects/{project['slug']}").status_code == 200
        assert client.get(f"/api/projects/{project['slug']}/issues").status_code == 200
        assert (
            client.get(f"/api/projects/{project['slug']}/milestones").status_code == 200
        )
        assert (
            client.get(f"/api/projects/{project['slug']}/kanban/columns").status_code
            == 200
        )
