"""Gitea 集成测试 —— 所有 GiteaClient 方法均 mock，不打真实服务。"""
from unittest.mock import patch, MagicMock

import pytest

from app.models.user import User
from app.models.project import Project
from app.services.project_service import ProjectService


def _mock_response(status=200, data=None):
    """Helper: 构造 mock httpx Response。"""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    return resp


def _mock_client(responses):
    """Helper: 构造按路径返回响应的 mock Gitea 客户端。"""
    client = MagicMock()

    def get(path, **kwargs):
        for prefix, resp in responses.items():
            if path.startswith(prefix):
                return resp
        return _mock_response(404, {"message": "not found"})

    client.get.side_effect = get
    return client


def _login(client, email="test@example.com", password="password123"):
    """Helper: 注册并登录，返回 headers。"""
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": email,
        "password": password,
    })
    resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _create_project(client, headers, name="Test Project"):
    """Helper: 创建项目，返回 slug。"""
    resp = client.post("/api/projects", json={
        "name": name,
        "description": "A test project",
        "visibility": "public",
    }, headers=headers)
    return resp.get_json()["project"]["slug"]


class TestRegisterGiteaBridge:
    """注册时的 Gitea 用户同步。"""

    @patch("app.services.auth_service.GiteaClient")
    def test_register_creates_gitea_user(self, mock_client, client):
        mock_client._is_available.return_value = True
        mock_client.admin_create_user.return_value = {"id": 42}
        mock_client.admin_create_user_token.return_value = "gitea-token-sha"

        resp = client.post("/api/auth/register", json={
            "username": "gituser",
            "email": "git@example.com",
            "password": "Password123!",
        })
        assert resp.status_code == 201

        mock_client.admin_create_user.assert_called_once()
        mock_client.admin_create_user_token.assert_called_once_with("gituser")

        user = User.query.filter_by(username="gituser").first()
        assert user is not None
        assert user.gitea_user_id == "42"
        assert user.gitea_token_encrypted is not None

    @patch("app.services.auth_service.GiteaClient")
    def test_register_degrades_when_gitea_down(self, mock_client, client):
        mock_client._is_available.return_value = False

        resp = client.post("/api/auth/register", json={
            "username": "nogituser",
            "email": "nogit@example.com",
            "password": "Password123!",
        })
        assert resp.status_code == 201

        mock_client.admin_create_user.assert_not_called()
        user = User.query.filter_by(username="nogituser").first()
        assert user is not None
        assert user.gitea_user_id is None
        assert user.gitea_token_encrypted is None


class TestRepoEndpoints:
    """repos 蓝图 CRUD 与权限。"""

    @patch("app.api.repos.GiteaClient")
    def test_create_repo(self, mock_client, client):
        mock_client._is_available.return_value = True
        mock_client._org_name.return_value = "codeersite"
        mock_client.admin_create_org.return_value = {"id": 1}
        mock_client.admin_create_repo.return_value = {
            "id": 99,
            "name": "test-project",
            "full_name": "codeersite/test-project",
            "default_branch": "main",
            "private": False,
            "html_url": "http://localhost:23000/codeersite/test-project",
            "ssh_url": "ssh://git@localhost:2222/codeersite/test-project.git",
            "clone_url": "http://localhost:23000/codeersite/test-project.git",
        }

        headers = _login(client)
        slug = _create_project(client, headers)

        resp = client.post(f"/api/projects/{slug}/repo", json={}, headers=headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["repo"]["full_name"] == "codeersite/test-project"

        project = Project.query.filter_by(slug=slug).first()
        assert project.gitea_repo_id == "99"
        assert project.gitea_full_name == "codeersite/test-project"

    @patch("app.api.repos.GiteaClient")
    def test_create_repo_non_owner_forbidden(self, mock_client, client):
        mock_client._is_available.return_value = True

        owner_headers = _login(client, email="owner@example.com", password="Password123!")
        slug = _create_project(client, owner_headers)

        # 注册另一个用户并尝试创建仓库
        client.post("/api/auth/register", json={
            "username": "memberuser",
            "email": "member@example.com",
            "password": "Password123!",
        })
        ProjectService.add_member(
            Project.query.filter_by(slug=slug).first().id,
            User.query.filter_by(username="memberuser").first().id,
            "member",
        )
        resp = client.post("/api/auth/login", json={
            "email": "member@example.com",
            "password": "Password123!",
        })
        member_headers = {"Authorization": f"Bearer {resp.get_json()['access_token']}"}

        resp = client.post(f"/api/projects/{slug}/repo", json={}, headers=member_headers)
        assert resp.status_code == 403
        mock_client.admin_create_repo.assert_not_called()

    @patch("app.api.repos.GiteaClient")
    def test_create_repo_gitea_unavailable(self, mock_client, client):
        mock_client._is_available.return_value = False

        headers = _login(client)
        slug = _create_project(client, headers)

        resp = client.post(f"/api/projects/{slug}/repo", json={}, headers=headers)
        assert resp.status_code == 503

    @patch("app.api.repos.GiteaClient")
    def test_get_repo(self, mock_client, client):
        mock_client.admin_get_repo.return_value = {
            "id": 99,
            "name": "test-project",
            "full_name": "codeersite/test-project",
            "description": "",
            "default_branch": "main",
            "private": False,
            "html_url": "http://localhost:23000/codeersite/test-project",
            "ssh_url": "ssh://git@localhost:2222/codeersite/test-project.git",
            "clone_url": "http://localhost:23000/codeersite/test-project.git",
            "stars_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "created_at": "2026-07-03T00:00:00Z",
            "updated_at": "2026-07-03T00:00:00Z",
        }

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.get(f"/api/projects/{slug}/repo", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["repo"]["full_name"] == "codeersite/test-project"

    def test_get_repo_not_exists(self, client):
        headers = _login(client)
        slug = _create_project(client, headers)

        resp = client.get(f"/api/projects/{slug}/repo", headers=headers)
        assert resp.status_code == 404

    @patch("app.api.repos.GiteaClient")
    def test_delete_repo(self, mock_client, client):
        mock_client.admin_delete_repo.return_value = True

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.delete(f"/api/projects/{slug}/repo", headers=headers)
        assert resp.status_code == 200

        mock_client.admin_delete_repo.assert_called_once_with("codeersite", "test-project")
        assert project.gitea_repo_id is None
        assert project.gitea_full_name is None


class TestRepoReadonlyEndpoints:
    """阶段 2 只读浏览端点。"""

    @patch("app.api.repos.GiteaClient")
    def test_list_branches(self, mock_client, client):
        mock_client.admin_get_repo.return_value = {"default_branch": "main"}
        mock_client.for_user.return_value = _mock_client({
            "/api/v1/repos/codeersite/test-project/branches": _mock_response(200, [
                {"name": "main", "commit": {"id": "abc123"}},
                {"name": "dev", "commit": {"id": "def456"}},
            ]),
        })

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.get(f"/api/projects/{slug}/repo/branches", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["branches"]) == 2
        assert data["branches"][0]["name"] == "main"

    @patch("app.api.repos.GiteaClient")
    def test_get_tree(self, mock_client, client):
        mock_client.admin_get_repo.return_value = {"default_branch": "main"}
        mock_client.for_user.return_value = _mock_client({
            "/api/v1/repos/codeersite/test-project/contents/": _mock_response(200, [
                {"name": "src", "path": "src", "type": "dir", "sha": "d1"},
                {"name": "README.md", "path": "README.md", "type": "file", "size": 42, "sha": "f1"},
            ]),
        })

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.get(f"/api/projects/{slug}/repo/tree", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ref"] == "main"
        assert len(data["tree"]) == 2
        assert data["tree"][0]["name"] == "src"

    @patch("app.api.repos.GiteaClient")
    def test_get_blob(self, mock_client, client):
        import base64

        content = base64.b64encode(b"hello world").decode()
        mock_client.admin_get_repo.return_value = {"default_branch": "main"}
        mock_client.for_user.return_value = _mock_client({
            "/api/v1/repos/codeersite/test-project/contents/README.md": _mock_response(200, {
                "name": "README.md",
                "path": "README.md",
                "sha": "f1",
                "size": 11,
                "encoding": "base64",
                "content": content,
                "html_url": "http://gitea/codeersite/test-project/blob/main/README.md",
                "download_url": None,
            }),
        })

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.get(f"/api/projects/{slug}/repo/blob?path=README.md", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["blob"]["content"] == "hello world"

    @patch("app.api.repos.GiteaClient")
    def test_list_commits(self, mock_client, client):
        mock_client.admin_get_repo.return_value = {"default_branch": "main"}
        mock_client.for_user.return_value = _mock_client({
            "/api/v1/repos/codeersite/test-project/commits": _mock_response(200, [
                {
                    "sha": "abc123",
                    "commit": {
                        "message": "init\n\nmore",
                        "author": {"name": "Dev", "email": "dev@example.com", "date": "2026-07-03T00:00:00Z"},
                    },
                    "html_url": "http://gitea/commit/abc123",
                }
            ]),
        })

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"

        resp = client.get(f"/api/projects/{slug}/repo/commits", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["commits"]) == 1
        assert data["commits"][0]["message"] == "init"

    @patch("app.api.repos.GiteaClient")
    @patch("app.api.repos.ReadOnlyGiteaClient")
    def test_public_repo_anonymous_tree(self, mock_ro_client, mock_client, client):
        """公开项目允许匿名访问 tree。"""
        mock_client.admin_get_repo.return_value = {"default_branch": "main"}
        mock_ro_instance = _mock_client({
            "/api/v1/repos/codeersite/test-project/contents/": _mock_response(200, [
                {"name": "README.md", "path": "README.md", "type": "file", "size": 10, "sha": "f1"},
            ]),
        })
        mock_ro_client.return_value = mock_ro_instance

        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"
        from app.extensions import db
        db.session.commit()

        with client.application.app_context():
            from flask import current_app

            current_app.config["GITEA_ADMIN_TOKEN"] = "anon-token"
            resp = client.get(f"/api/projects/{slug}/repo/tree")

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["tree"]) == 1

    def test_private_repo_anonymous_forbidden(self, client):
        """私有项目匿名访问只读端点返回 403。"""
        headers = _login(client)
        slug = _create_project(client, headers)
        project = Project.query.filter_by(slug=slug).first()
        project.visibility = "private"
        project.gitea_repo_id = "99"
        project.gitea_full_name = "codeersite/test-project"
        from app.extensions import db
        db.session.commit()

        resp = client.get(f"/api/projects/{slug}/repo/tree")
        assert resp.status_code == 403
