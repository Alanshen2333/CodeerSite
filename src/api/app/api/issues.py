from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.issue import (
    IssueCreateSchema,
    IssueUpdateSchema,
    TimeEntryCreateSchema,
)
from app.services.issue_service import IssueService
from app.services.project_service import ProjectService

issues_bp = Blueprint("issues", __name__)


def _get_project_or_404(slug: str):
    project = ProjectService.get_project(slug=slug)
    if not project:
        return None, (jsonify(error="Not Found", message="Project not found."), 404)
    return project, None


@issues_bp.route("/projects/<slug>/issues", methods=["GET"])
@jwt_required(optional=True)
def list_issues(slug):
    """List issues for a project."""
    project, err = _get_project_or_404(slug)
    if err:
        return err
    user = get_current_user()
    if not ProjectService.can_view(project, user.id if user else None):
        return jsonify(error="Not Found", message="Project not found."), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    priority = request.args.get("priority")
    assignee_id = request.args.get("assignee_id")
    milestone_id = request.args.get("milestone_id")
    tag_id = request.args.get("tag_id")
    sort = request.args.get("sort", "newest")

    # milestone_id can be "none" to filter for issues without milestone
    if milestone_id == "none":
        milestone_id = None

    result = IssueService.get_issues(
        project_id=project.id,
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        milestone_id=milestone_id,
        tag_id=tag_id,
        sort=sort,
    )
    stats = IssueService.get_issue_stats(project.id)
    return jsonify(
        issues=[i.to_dict() for i in result.items],
        stats=stats,
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@issues_bp.route("/projects/<slug>/issues", methods=["POST"])
@jwt_required()
def create_issue(slug):
    """Create a new issue."""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    role = ProjectService.get_user_role(project.id, user.id)
    if not role:
        return jsonify(error="Forbidden", message="You must be a project member."), 403

    try:
        data = IssueCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    issue = IssueService.create_issue(
        project_id=project.id,
        author_id=user.id,
        title=data["title"],
        body=data.get("body"),
        assignee_id=data.get("assignee_id"),
        priority=data.get("priority", "medium"),
        milestone_id=data.get("milestone_id"),
        tag_ids=data.get("tag_ids"),
        time_estimate=data.get("time_estimate"),
    )
    return jsonify(issue=issue.to_dict()), 201


@issues_bp.route("/projects/<slug>/issues/<int:issue_number>", methods=["GET"])
@jwt_required(optional=True)
def get_issue(slug, issue_number):
    """Get a single issue."""
    project, err = _get_project_or_404(slug)
    if err:
        return err
    user = get_current_user()
    if not ProjectService.can_view(project, user.id if user else None):
        return jsonify(error="Not Found", message="Project not found."), 404

    issue = IssueService.get_issue(project_id=project.id, issue_number=issue_number)
    if not issue:
        return jsonify(error="Not Found", message="Issue not found."), 404
    return jsonify(issue=issue.to_dict()), 200


@issues_bp.route("/projects/<slug>/issues/<int:issue_number>", methods=["PATCH"])
@jwt_required()
def update_issue(slug, issue_number):
    """Update an issue."""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    issue = IssueService.get_issue(project_id=project.id, issue_number=issue_number)
    if not issue:
        return jsonify(error="Not Found", message="Issue not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if not role:
        return jsonify(error="Forbidden", message="You must be a project member."), 403

    try:
        data = IssueUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    # 部分更新：剔除未提供字段（None）。但 time_estimate / assignee_id /
    # milestone_id 的 allow_none 字段需保留显式 None（用于清空）。
    allow_none_fields = {"time_estimate", "assignee_id", "milestone_id"}
    update_data = {
        k: v for k, v in data.items() if v is not None or k in allow_none_fields
    }
    issue = IssueService.update_issue(issue, **update_data)
    return jsonify(issue=issue.to_dict()), 200


@issues_bp.route(
    "/projects/<slug>/issues/<int:issue_number>/time-entries", methods=["GET"]
)
@jwt_required()
def list_time_entries(slug, issue_number):
    """列出某 Issue 的耗时条目。需项目成员。"""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    issue = IssueService.get_issue(project_id=project.id, issue_number=issue_number)
    if not issue:
        return jsonify(error="Not Found", message="Issue not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if not role:
        return jsonify(error="Forbidden", message="You must be a project member."), 403

    entries = IssueService.get_time_entries(issue)
    return jsonify(
        time_entries=[e.to_dict() for e in entries],
        total=len(entries),
    ), 200


@issues_bp.route(
    "/projects/<slug>/issues/<int:issue_number>/time-entries", methods=["POST"]
)
@jwt_required()
def create_time_entry(slug, issue_number):
    """记录一段耗时。需项目成员。"""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    issue = IssueService.get_issue(project_id=project.id, issue_number=issue_number)
    if not issue:
        return jsonify(error="Not Found", message="Issue not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if not role:
        return jsonify(error="Forbidden", message="You must be a project member."), 403

    try:
        data = TimeEntryCreateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    entry = IssueService.add_time_entry(
        issue=issue,
        user_id=user.id,
        seconds=data["seconds"],
        note=data.get("note"),
    )
    return jsonify(entry=entry.to_dict(), issue=issue.to_dict()), 201


@issues_bp.route("/projects/<slug>/issues/<int:issue_number>", methods=["DELETE"])
@jwt_required()
def delete_issue(slug, issue_number):
    """Delete an issue. Author or project admin/owner."""
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err

    issue = IssueService.get_issue(project_id=project.id, issue_number=issue_number)
    if not issue:
        return jsonify(error="Not Found", message="Issue not found."), 404

    role = ProjectService.get_user_role(project.id, user.id)
    if issue.author_id != user.id and role not in ("admin", "owner"):
        return jsonify(error="Forbidden", message="You cannot delete this issue."), 403

    IssueService.delete_issue(issue)
    return jsonify(message="Issue deleted."), 200
