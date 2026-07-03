"""Repo blueprint: Project ↔ Gitea 仓库关联。"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.schemas.repo import RepoCreateSchema
from app.services.gitea_client import GiteaClient, _org_name
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
        return jsonify(error="Not Found", message="Project has no associated repository."), 404

    repo = GiteaClient.admin_get_repo(
        org=project.gitea_full_name.split("/")[0],
        name=project.gitea_full_name.split("/")[-1],
    )
    if repo is None:
        return (
            jsonify(error="Service Unavailable", message="Gitea is unavailable or repository not found."),
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
        return jsonify(error="Forbidden", message="Only project owner/admin can create repository."), 403

    if project.gitea_repo_id:
        return jsonify(error="Conflict", message="Repository already exists for this project."), 409

    if not GiteaClient._is_available():
        return jsonify(error="Service Unavailable", message="Gitea is not available."), 503

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
        return jsonify(error="Service Unavailable", message="Failed to create repository in Gitea."), 503

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
        return jsonify(error="Forbidden", message="Only project owner can delete repository."), 403

    if not project.gitea_full_name:
        return jsonify(error="Not Found", message="Project has no associated repository."), 404

    org = project.gitea_full_name.split("/")[0]
    name = project.gitea_full_name.split("/")[-1]
    deleted = GiteaClient.admin_delete_repo(org, name)
    if not deleted and GiteaClient._is_available():
        return jsonify(error="Service Unavailable", message="Failed to delete repository in Gitea."), 503

    project.gitea_repo_id = None
    project.gitea_full_name = None
    from app.extensions import db

    db.session.commit()

    return jsonify(message="Repository deleted."), 200
