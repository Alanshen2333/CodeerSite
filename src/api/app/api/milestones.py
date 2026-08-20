from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.milestone import MilestoneCreateSchema, MilestoneUpdateSchema
from app.services.milestone_service import MilestoneService
from app.services.project_service import ProjectService

milestones_bp = Blueprint("milestones", __name__)


def _get_project_or_404(slug):
    project = ProjectService.get_project(slug=slug)
    if not project:
        return None, (jsonify(error="Not Found", message="Project not found."), 404)
    return project, None


def _check_member(project, user):
    role = ProjectService.get_user_role(project.id, user.id)
    if not role:
        return jsonify(error="Forbidden", message="You must be a project member."), 403
    return None


@milestones_bp.route("/projects/<slug>/milestones", methods=["GET"])
@jwt_required(optional=True)
def list_milestones(slug):
    project, err = _get_project_or_404(slug)
    if err:
        return err
    user = get_current_user()
    if not ProjectService.can_view(project, user.id if user else None):
        return jsonify(error="Not Found", message="Project not found."), 404
    milestones = MilestoneService.get_milestones(project.id)
    return jsonify(milestones=[m.to_dict() for m in milestones]), 200


@milestones_bp.route("/projects/<slug>/milestones", methods=["POST"])
@jwt_required()
def create_milestone(slug):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err
    if err2 := _check_member(project, user):
        return err2

    try:
        data = MilestoneCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    milestone = MilestoneService.create_milestone(
        project_id=project.id,
        title=data["title"],
        description=data.get("description"),
        due_date=data.get("due_date"),
    )
    return jsonify(milestone=milestone.to_dict()), 201


@milestones_bp.route("/projects/<slug>/milestones/<milestone_id>", methods=["PATCH"])
@jwt_required()
def update_milestone(slug, milestone_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err
    if err2 := _check_member(project, user):
        return err2

    milestone = MilestoneService.get_milestone(milestone_id)
    if not milestone or milestone.project_id != project.id:
        return jsonify(error="Not Found", message="Milestone not found."), 404

    try:
        data = MilestoneUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    update_data = {k: v for k, v in data.items() if v is not None}
    milestone = MilestoneService.update_milestone(milestone, **update_data)
    return jsonify(milestone=milestone.to_dict()), 200


@milestones_bp.route("/projects/<slug>/milestones/<milestone_id>", methods=["DELETE"])
@jwt_required()
def delete_milestone(slug, milestone_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err:
        return err
    role = ProjectService.get_user_role(project.id, user.id)
    if role not in ("owner", "admin"):
        return jsonify(
            error="Forbidden", message="Only owner/admin can delete milestones."
        ), 403

    milestone = MilestoneService.get_milestone(milestone_id)
    if not milestone or milestone.project_id != project.id:
        return jsonify(error="Not Found", message="Milestone not found."), 404

    MilestoneService.delete_milestone(milestone)
    return jsonify(message="Milestone deleted."), 200
