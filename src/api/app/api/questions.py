from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.extensions import db
from app.models.question import Question
from app.schemas.question import QuestionCreateSchema, QuestionUpdateSchema
from app.services.question_service import QuestionService

questions_bp = Blueprint("questions", __name__)


@questions_bp.route("", methods=["GET"])
def list_questions():
    """List questions with pagination, sorting, and filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)
    sort = request.args.get("sort", "newest")
    tag = request.args.get("tag")
    filter_type = request.args.get("filter")

    result = QuestionService.get_questions(
        page=page,
        per_page=per_page,
        sort=sort,
        tag_slug=tag,
        filter_type=filter_type,
    )
    return jsonify(
        questions=[q.to_list_dict() for q in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@questions_bp.route("/<question_id>", methods=["GET"])
def get_question(question_id):
    """Get a single question by ID."""
    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404

    # Increment view count
    QuestionService.increment_view(question)

    return jsonify(question=question.to_dict()), 200


@questions_bp.route("", methods=["POST"])
@jwt_required()
def create_question():
    """Create a new question."""
    user = get_current_user()
    try:
        data = QuestionCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    question = QuestionService.create_question(
        author_id=user.id,
        title=data["title"],
        body=data["body"],
        tag_ids=data.get("tag_ids", []),
    )
    return jsonify(question=question.to_dict()), 201


@questions_bp.route("/<question_id>", methods=["PATCH"])
@jwt_required()
def update_question(question_id):
    """Update a question. Only the author can update."""
    user = get_current_user()
    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404
    if question.author_id != user.id:
        return jsonify(error="Forbidden", message="You can only edit your own questions."), 403

    try:
        data = QuestionUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    question = QuestionService.update_question(
        question=question,
        title=data.get("title"),
        body=data.get("body"),
        tag_ids=data.get("tag_ids"),
    )
    return jsonify(question=question.to_dict()), 200


@questions_bp.route("/<question_id>", methods=["DELETE"])
@jwt_required()
def delete_question(question_id):
    """Delete a question. Only the author or admin can delete."""
    user = get_current_user()
    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404
    if question.author_id != user.id and user.role not in ("moderator", "admin"):
        return jsonify(error="Forbidden", message="You can only delete your own questions."), 403

    QuestionService.delete_question(question)
    return jsonify(message="Question deleted."), 200


@questions_bp.route("/<question_id>/close", methods=["POST"])
@jwt_required()
def close_question(question_id):
    """Close a question. Only the author or moderator/admin can close."""
    user = get_current_user()
    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404
    if question.author_id != user.id and user.role not in ("moderator", "admin"):
        return jsonify(error="Forbidden", message="You cannot close this question."), 403

    question = QuestionService.close_question(question)
    return jsonify(question=question.to_dict()), 200


@questions_bp.route("/<question_id>/reopen", methods=["POST"])
@jwt_required()
def reopen_question(question_id):
    """Reopen a question. Only the author or moderator/admin can reopen."""
    user = get_current_user()
    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404
    if question.author_id != user.id and user.role not in ("moderator", "admin"):
        return jsonify(error="Forbidden", message="You cannot reopen this question."), 403

    question = QuestionService.reopen_question(question)
    return jsonify(question=question.to_dict()), 200


@questions_bp.route("/<question_id>/pin", methods=["POST"])
@jwt_required()
def toggle_pin(question_id):
    """Toggle pin status. Admin/moderator only."""
    user = get_current_user()
    if user.role not in ("moderator", "admin"):
        return jsonify(error="Forbidden", message="Moderator access required."), 403

    question = QuestionService.get_question(question_id)
    if not question:
        return jsonify(error="Not Found", message="Question not found."), 404

    question = QuestionService.toggle_pin(question)
    return jsonify(question=question.to_dict()), 200
