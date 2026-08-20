from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.project import ProjectCreateSchema, ProjectUpdateSchema
from app.schemas.member import AddMemberSchema, UpdateMemberSchema
from app.services.project_service import ProjectService

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_projects():
    """List projects."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sort = request.args.get("sort", "newest")
    visibility = request.args.get("visibility")
    user = get_current_user()  # optional=True：未登录为 None

    result = ProjectService.get_projects(
        page=page,
        per_page=per_page,
        sort=sort,
        visibility=visibility,
        user_id=user.id if user else None,
    )
    starred_ids = (
        ProjectService.get_starred_project_ids(user.id, [p.id for p in result.items])
        if user
        else set()
    )
    projects = []
    for p in result.items:
        d = p.to_dict()
        d["starred"] = p.id in starred_ids
        projects.append(d)
    return jsonify(
        projects=projects,
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """Create a new project."""
    user = get_current_user()
    try:
        data = ProjectCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    project = ProjectService.create_project(
        owner_id=user.id,
        name=data["name"],
        description=data.get("description"),
        visibility=data.get("visibility", "public"),
    )
    return jsonify(project=project.to_dict()), 201


@projects_bp.route("/<slug>", methods=["GET"])
@jwt_required(optional=True)
def get_project(slug):
    """Get project by slug."""
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404
    user = get_current_user()
    if not ProjectService.can_view(project, user.id if user else None):
        return jsonify(error="Not Found", message="Project not found."), 404
    data = project.to_dict()
    data["starred"] = ProjectService.is_starred(project.id, user.id) if user else False
    return jsonify(project=data), 200


@projects_bp.route("/<slug>", methods=["PATCH"])
@jwt_required()
def update_project(slug):
    """Update project. Owner or admin only."""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if role not in ("owner", "admin"):
        return jsonify(
            error="Forbidden", message="Only project owner/admin can update."
        ), 403

    try:
        data = ProjectUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    project = ProjectService.update_project(
        project,
        name=data.get("name"),
        description=data.get("description"),
        visibility=data.get("visibility"),
    )
    return jsonify(project=project.to_dict()), 200


@projects_bp.route("/<slug>", methods=["DELETE"])
@jwt_required()
def delete_project(slug):
    """Delete project. Owner only."""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if role != "owner":
        return jsonify(
            error="Forbidden", message="Only the project owner can delete."
        ), 403

    ProjectService.delete_project(project)
    return jsonify(message="Project deleted."), 200


# -- Members --
@projects_bp.route("/<slug>/members", methods=["GET"])
@jwt_required(optional=True)
def list_members(slug):
    """List project members."""
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404
    user = get_current_user()
    if not ProjectService.can_view(project, user.id if user else None):
        return jsonify(error="Not Found", message="Project not found."), 404
    members = ProjectService.get_members(project.id)
    return jsonify(members=[m.to_dict() for m in members]), 200


@projects_bp.route("/<slug>/members", methods=["POST"])
@jwt_required()
def add_member(slug):
    """Add a member to project. Owner/admin only."""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if role not in ("owner", "admin"):
        return jsonify(
            error="Forbidden", message="Only owner/admin can add members."
        ), 403

    try:
        data = AddMemberSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        member = ProjectService.add_member(
            project.id, data["user_id"], data.get("role", "member")
        )
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    return jsonify(member=member.to_dict()), 201


@projects_bp.route("/<slug>/members/<user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(slug, user_id):
    """Remove a member. Owner/admin only."""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if role not in ("owner", "admin"):
        return jsonify(
            error="Forbidden", message="Only owner/admin can remove members."
        ), 403

    try:
        ProjectService.remove_member(project.id, user_id)
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400

    return jsonify(message="Member removed."), 200


@projects_bp.route("/<slug>/members/<user_id>", methods=["PATCH"])
@jwt_required()
def update_member_role(slug, user_id):
    """Update member role. Owner only."""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if role != "owner":
        return jsonify(error="Forbidden", message="Only owner can change roles."), 403

    try:
        data = UpdateMemberSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        member = ProjectService.update_member_role(project.id, user_id, data["role"])
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400

    return jsonify(member=member.to_dict()), 200


# -- Star --
@projects_bp.route("/<slug>/star", methods=["POST"])
@jwt_required()
def star_project(slug):
    """切换项目的 star。"""
    user = get_current_user()
    project = ProjectService.get_project(slug=slug)
    if not project:
        return jsonify(error="Not Found", message="Project not found."), 404
    if not ProjectService.can_view(project, user.id):
        return jsonify(error="Not Found", message="Project not found."), 404
    starred = ProjectService.toggle_star(project, user.id)
    return jsonify(starred=starred, star_count=project.star_count), 200
