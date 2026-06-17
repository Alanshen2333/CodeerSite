from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.kanban import KanbanColumnCreateSchema, KanbanCardCreateSchema, KanbanCardMoveSchema
from app.services.kanban_service import KanbanService
from app.services.project_service import ProjectService

kanban_bp = Blueprint("kanban", __name__)


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


# -- Columns --
@kanban_bp.route("/projects/<slug>/kanban/columns", methods=["GET"])
def list_columns(slug):
    project, err = _get_project_or_404(slug)
    if err: return err

    columns = KanbanService.get_columns(project.id)
    return jsonify(columns=[
        {**c.to_dict(), "cards": [card.to_dict() for card in c.cards]}
        for c in columns
    ]), 200


@kanban_bp.route("/projects/<slug>/kanban/columns", methods=["POST"])
@jwt_required()
def create_column(slug):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    try:
        data = KanbanColumnCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    col = KanbanService.create_column(project.id, data["title"])
    return jsonify(column=col.to_dict()), 201


@kanban_bp.route("/projects/<slug>/kanban/columns/<column_id>", methods=["PATCH"])
@jwt_required()
def update_column(slug, column_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    col = KanbanService.get_column(column_id)
    if not col or col.project_id != project.id:
        return jsonify(error="Not Found", message="Column not found."), 404

    data = request.get_json() or {}
    col = KanbanService.update_column(col, title=data.get("title"))
    return jsonify(column=col.to_dict()), 200


@kanban_bp.route("/projects/<slug>/kanban/columns/<column_id>", methods=["DELETE"])
@jwt_required()
def delete_column(slug, column_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    col = KanbanService.get_column(column_id)
    if not col or col.project_id != project.id:
        return jsonify(error="Not Found", message="Column not found."), 404

    KanbanService.delete_column(col)
    return jsonify(message="Column deleted."), 200


@kanban_bp.route("/projects/<slug>/kanban/columns/reorder", methods=["POST"])
@jwt_required()
def reorder_columns(slug):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    data = request.get_json() or {}
    column_ids = data.get("column_ids", [])
    KanbanService.reorder_columns(project.id, column_ids)
    return jsonify(message="Columns reordered."), 200


# -- Cards --
@kanban_bp.route("/projects/<slug>/kanban/columns/<column_id>/cards", methods=["POST"])
@jwt_required()
def create_card(slug, column_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    col = KanbanService.get_column(column_id)
    if not col or col.project_id != project.id:
        return jsonify(error="Not Found", message="Column not found."), 404

    try:
        data = KanbanCardCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    card = KanbanService.create_card(column_id, data["title"], data.get("issue_id"))
    return jsonify(card=card.to_dict()), 201


@kanban_bp.route("/projects/<slug>/kanban/cards/<card_id>", methods=["PATCH"])
@jwt_required()
def update_card(slug, card_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    card = KanbanService.get_card(card_id)
    if not card:
        return jsonify(error="Not Found", message="Card not found."), 404

    data = request.get_json() or {}
    card = KanbanService.update_card(card, title=data.get("title"))
    return jsonify(card=card.to_dict()), 200


@kanban_bp.route("/projects/<slug>/kanban/cards/<card_id>", methods=["DELETE"])
@jwt_required()
def delete_card(slug, card_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    card = KanbanService.get_card(card_id)
    if not card:
        return jsonify(error="Not Found", message="Card not found."), 404

    KanbanService.delete_card(card)
    return jsonify(message="Card deleted."), 200


@kanban_bp.route("/projects/<slug>/kanban/cards/<card_id>/move", methods=["POST"])
@jwt_required()
def move_card(slug, card_id):
    user = get_current_user()
    project, err = _get_project_or_404(slug)
    if err: return err
    if err2 := _check_member(project, user): return err2

    card = KanbanService.get_card(card_id)
    if not card:
        return jsonify(error="Not Found", message="Card not found."), 404

    try:
        data = KanbanCardMoveSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    card = KanbanService.move_card(card, data["column_id"], data["position"])
    return jsonify(card=card.to_dict()), 200
