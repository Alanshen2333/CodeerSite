"""Repo blueprint: Project ↔ Gitea 仓库关联。"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.schemas.repo import RepoCreateSchema
from app.services.gitea_client import GiteaClient, ReadOnlyGiteaClient, _org_name
from app.services.project_service import ProjectService

repos_bp = Blueprint("repos", __name__)


def _get_project_or_404(slug: str):
    project = ProjectService.get_project(slug=slug)
    if not project:
        return None, (jsonify(error="Not Found", message="Project not found."), 404)
    return project, None


def _can_access_repo(project, user) -> bool:
    """公开项目任何人可见；私有项目仅成员可见。"""
    if project.visibility == "public":
        return True
    if user is None:
        return False
    return ProjectService.get_user_role(project.id, user.id) is not None


def _get_read_client(project, user):
    """为只读请求构造 Gitea 客户端。

    已登录用户优先使用自己的 token；公开项目匿名访问使用 GITEA_PUBLIC_READONLY_TOKEN
    或回退到 GITEA_ADMIN_TOKEN。
    """
    if user:
        client = GiteaClient.for_user(user)
        if client:
            return client
    if project.visibility == "public":
        token = current_app.config.get(
            "GITEA_PUBLIC_READONLY_TOKEN"
        ) or current_app.config.get("GITEA_ADMIN_TOKEN")
        if token:
            return ReadOnlyGiteaClient(token)
    return None


def _get_default_branch(project) -> str | None:
    """从 Gitea 获取仓库默认分支。"""
    if not project.gitea_full_name:
        return None
    org, name = project.gitea_full_name.split("/")
    repo = GiteaClient.admin_get_repo(org, name)
    if repo:
        return repo.get("default_branch") or "main"
    return None


@repos_bp.route("/projects/<slug>/repo", methods=["GET"])
@jwt_required(optional=True)
def get_repo(slug):
    """获取项目关联的 Gitea 仓库元信息。"""
    project, err = _get_project_or_404(slug)
    if err:
        return err

    user = get_current_user()
    if not _can_access_repo(project, user):
        return jsonify(error="Forbidden", message="Private project."), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    repo = GiteaClient.admin_get_repo(
        org=project.gitea_full_name.split("/")[0],
        name=project.gitea_full_name.split("/")[-1],
    )
    if repo is None:
        return (
            jsonify(
                error="Service Unavailable",
                message="Gitea is unavailable or repository not found.",
            ),
            503,
        )

    return jsonify(
        repo={
            "id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "default_branch": repo.get("default_branch"),
            "private": repo.get("private"),
            "html_url": repo.get("html_url"),
            "ssh_url": repo.get("ssh_url"),
            "clone_url": repo.get("clone_url"),
            "stars_count": repo.get("stars_count", 0),
            "forks_count": repo.get("forks_count", 0),
            "open_issues_count": repo.get("open_issues_count", 0),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
        }
    ), 200


@repos_bp.route("/projects/<slug>/repo", methods=["POST"])
@jwt_required()
def create_repo(slug):
    """为项目创建 Gitea 仓库。仅 owner/admin 可操作。"""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    role = ProjectService.get_user_role(project.id, user.id)
    if role not in ("owner", "admin"):
        return jsonify(
            error="Forbidden", message="Only project owner/admin can create repository."
        ), 403

    if project.gitea_repo_id:
        return jsonify(
            error="Conflict", message="Repository already exists for this project."
        ), 409

    if not GiteaClient._is_available():
        return jsonify(
            error="Service Unavailable", message="Gitea is not available."
        ), 503

    try:
        data = RepoCreateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    org = _org_name()
    repo_name = data.get("name") or project.slug
    description = data.get("description") or project.description
    private = data.get("private", project.visibility == "private")

    # 确保 org 存在
    GiteaClient.admin_create_org(org)

    repo = GiteaClient.admin_create_repo(
        org=org,
        name=repo_name,
        description=description,
        private=private,
    )
    if repo is None:
        return jsonify(
            error="Service Unavailable", message="Failed to create repository in Gitea."
        ), 503

    project.gitea_repo_id = str(repo.get("id"))
    project.gitea_full_name = repo.get("full_name") or f"{org}/{repo_name}"
    from app.extensions import db

    db.session.commit()

    return jsonify(
        repo={
            "id": project.gitea_repo_id,
            "name": repo.get("name"),
            "full_name": project.gitea_full_name,
            "default_branch": repo.get("default_branch"),
            "private": repo.get("private"),
            "html_url": repo.get("html_url"),
            "ssh_url": repo.get("ssh_url"),
            "clone_url": repo.get("clone_url"),
        }
    ), 201


@repos_bp.route("/projects/<slug>/repo", methods=["DELETE"])
@jwt_required()
def delete_repo(slug):
    """删除项目关联的 Gitea 仓库。仅 owner 可操作。"""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    role = ProjectService.get_user_role(project.id, user.id)
    if role != "owner":
        return jsonify(
            error="Forbidden", message="Only project owner can delete repository."
        ), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    org = project.gitea_full_name.split("/")[0]
    name = project.gitea_full_name.split("/")[-1]
    deleted = GiteaClient.admin_delete_repo(org, name)
    if not deleted and GiteaClient._is_available():
        return jsonify(
            error="Service Unavailable", message="Failed to delete repository in Gitea."
        ), 503

    project.gitea_repo_id = None
    project.gitea_full_name = None
    from app.extensions import db

    db.session.commit()

    return jsonify(message="Repository deleted."), 200


@repos_bp.route("/projects/<slug>/repo/branches", methods=["GET"])
@jwt_required(optional=True)
def list_branches(slug):
    """列出仓库分支。"""
    project, err = _get_project_or_404(slug)
    if err:
        return err

    user = get_current_user()
    if not _can_access_repo(project, user):
        return jsonify(error="Forbidden", message="Private project."), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    client = _get_read_client(project, user)
    if client is None:
        return jsonify(
            error="Service Unavailable", message="Gitea token not available."
        ), 503

    org, name = project.gitea_full_name.split("/")
    resp = client.get(f"/api/v1/repos/{org}/{name}/branches")
    if resp is None or resp.status_code != 200:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch branches."
        ), 503

    data = resp.json()
    branches = [
        {
            "name": b.get("name"),
            "commit": b.get("commit", {}).get("id")
            if isinstance(b.get("commit"), dict)
            else None,
        }
        for b in (data if isinstance(data, list) else [])
    ]
    return jsonify(branches=branches), 200


@repos_bp.route("/projects/<slug>/repo/tree", methods=["GET"])
@jwt_required(optional=True)
def get_tree(slug):
    """获取文件树。query: ref (默认 default_branch), path (默认根目录)。"""
    project, err = _get_project_or_404(slug)
    if err:
        return err

    user = get_current_user()
    if not _can_access_repo(project, user):
        return jsonify(error="Forbidden", message="Private project."), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    client = _get_read_client(project, user)
    if client is None:
        return jsonify(
            error="Service Unavailable", message="Gitea token not available."
        ), 503

    ref = request.args.get("ref") or _get_default_branch(project) or "main"
    path = request.args.get("path", "")
    org, name = project.gitea_full_name.split("/")

    resp = client.get(
        f"/api/v1/repos/{org}/{name}/contents/{path}",
        params={"ref": ref},
    )
    if resp is None:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch tree."
        ), 503

    if resp.status_code == 404:
        return jsonify(error="Not Found", message="Path not found."), 404
    if resp.status_code != 200:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch tree."
        ), 503

    data = resp.json()
    items = data if isinstance(data, list) else [data]
    entries = [
        {
            "name": item.get("name"),
            "path": item.get("path"),
            "type": item.get("type"),  # file / dir / symlink / submodule
            "size": item.get("size") if item.get("type") == "file" else None,
            "sha": item.get("sha"),
            "download_url": item.get("download_url"),
        }
        for item in items
    ]
    # 目录在前，按名称排序
    entries.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))
    return jsonify(tree=entries, ref=ref, path=path), 200


@repos_bp.route("/projects/<slug>/repo/blob", methods=["GET"])
@jwt_required(optional=True)
def get_blob(slug):
    """获取文件内容。query: ref, path。"""
    project, err = _get_project_or_404(slug)
    if err:
        return err

    user = get_current_user()
    if not _can_access_repo(project, user):
        return jsonify(error="Forbidden", message="Private project."), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    client = _get_read_client(project, user)
    if client is None:
        return jsonify(
            error="Service Unavailable", message="Gitea token not available."
        ), 503

    ref = request.args.get("ref") or _get_default_branch(project) or "main"
    path = request.args.get("path", "")
    if not path:
        return jsonify(error="Bad Request", message="path is required."), 400

    org, name = project.gitea_full_name.split("/")
    resp = client.get(
        f"/api/v1/repos/{org}/{name}/contents/{path}",
        params={"ref": ref} if ref else None,
    )
    if resp is None:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch blob."
        ), 503

    if resp.status_code == 404:
        return jsonify(error="Not Found", message="File not found."), 404
    if resp.status_code != 200:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch blob."
        ), 503

    data = resp.json()
    # Gitea contents API 对文件返回 dict；内容可能是 base64 编码
    if isinstance(data, list):
        return jsonify(error="Bad Request", message="Path is a directory."), 400

    content = data.get("content", "")
    encoding = data.get("encoding", "")
    if encoding == "base64":
        import base64

        try:
            content = base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            content = ""

    return jsonify(
        blob={
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "content": content,
            "encoding": "utf-8" if encoding == "base64" else encoding,
            "html_url": data.get("html_url"),
            "download_url": data.get("download_url"),
        }
    ), 200


@repos_bp.route("/projects/<slug>/repo/commits", methods=["GET"])
@jwt_required(optional=True)
def list_commits(slug):
    """列出 commit 历史。query: ref (分支/tag/sha), page, per_page。"""
    project, err = _get_project_or_404(slug)
    if err:
        return err

    user = get_current_user()
    if not _can_access_repo(project, user):
        return jsonify(error="Forbidden", message="Private project."), 403

    if not project.gitea_full_name:
        return jsonify(
            error="Not Found", message="Project has no associated repository."
        ), 404

    client = _get_read_client(project, user)
    if client is None:
        return jsonify(
            error="Service Unavailable", message="Gitea token not available."
        ), 503

    ref = request.args.get("ref") or _get_default_branch(project) or "main"
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 30))
    except ValueError:
        return jsonify(error="Bad Request", message="Invalid pagination."), 400

    org, name = project.gitea_full_name.split("/")
    resp = client.get(
        f"/api/v1/repos/{org}/{name}/commits",
        params={"sha": ref, "page": page, "limit": per_page},
    )
    if resp is None or resp.status_code != 200:
        return jsonify(
            error="Service Unavailable", message="Failed to fetch commits."
        ), 503

    data = resp.json()
    commits = data if isinstance(data, list) else data.get("commits", [])
    results = []
    for c in commits:
        commit_data = c.get("commit", {}) if isinstance(c.get("commit"), dict) else {}
        author = (
            commit_data.get("author", {})
            if isinstance(commit_data.get("author"), dict)
            else {}
        )
        results.append(
            {
                "sha": c.get("sha"),
                "message": commit_data.get("message", "").split("\n")[0],
                "full_message": commit_data.get("message", ""),
                "author_name": author.get("name"),
                "author_email": author.get("email"),
                "date": author.get("date"),
                "html_url": c.get("html_url"),
            }
        )

    return jsonify(commits=results, page=page, per_page=per_page, ref=ref), 200
