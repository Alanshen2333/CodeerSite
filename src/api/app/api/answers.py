from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.answer import AnswerCreateSchema, AnswerUpdateSchema
from app.services.answer_service import AnswerService

answers_bp = Blueprint("answers", __name__)


@answers_bp.route("", methods=["GET"])
def list_answers():
    """List answers for a question."""
    question_id = request.args.get("question_id")
    if not question_id:
        return jsonify(error="Bad Request", message="question_id is required."), 400

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = AnswerService.get_answers(question_id, page=page, per_page=per_page)
    return jsonify(
        answers=[a.to_list_dict() for a in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@answers_bp.route("", methods=["POST"])
@jwt_required()
def create_answer():
    """Create an answer."""
    user = get_current_user()
    try:
        data = AnswerCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        answer = AnswerService.create_answer(
            question_id=data["question_id"],
            author_id=user.id,
            body=data["body"],
        )
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400

    return jsonify(answer=answer.to_dict()), 201


@answers_bp.route("/<answer_id>", methods=["PATCH"])
@jwt_required()
def update_answer(answer_id):
    """Update an answer. Only the author can update."""
    user = get_current_user()
    answer = AnswerService.get_answer(answer_id)
    if not answer:
        return jsonify(error="Not Found", message="Answer not found."), 404
    if answer.author_id != user.id:
        return jsonify(error="Forbidden", message="You can only edit your own answers."), 403

    try:
        data = AnswerUpdateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    answer = AnswerService.update_answer(answer, data["body"])
    return jsonify(answer=answer.to_dict()), 200


@answers_bp.route("/<answer_id>", methods=["DELETE"])
@jwt_required()
def delete_answer(answer_id):
    """Delete an answer. Only the author or admin can delete."""
    user = get_current_user()
    answer = AnswerService.get_answer(answer_id)
    if not answer:
        return jsonify(error="Not Found", message="Answer not found."), 404
    if answer.author_id != user.id and user.role not in ("moderator", "admin"):
        return jsonify(error="Forbidden", message="You can only delete your own answers."), 403

    AnswerService.delete_answer(answer)
    return jsonify(message="Answer deleted."), 200


@answers_bp.route("/<answer_id>/accept", methods=["POST"])
@jwt_required()
def accept_answer(answer_id):
    """Accept an answer (question author only)."""
    user = get_current_user()
    answer = AnswerService.get_answer(answer_id)
    if not answer:
        return jsonify(error="Not Found", message="Answer not found."), 404

    try:
        answer = AnswerService.accept_answer(answer, user.id)
    except PermissionError as e:
        return jsonify(error="Forbidden", message=str(e)), 403
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400

    return jsonify(answer=answer.to_dict()), 200


@answers_bp.route("/<answer_id>/accept", methods=["DELETE"])
@jwt_required()
def unaccept_answer(answer_id):
    """Un-accept an answer (question author only)."""
    user = get_current_user()
    answer = AnswerService.get_answer(answer_id)
    if not answer:
        return jsonify(error="Not Found", message="Answer not found."), 404

    try:
        AnswerService.unaccept_answer(answer, user.id)
    except PermissionError as e:
        return jsonify(error="Forbidden", message=str(e)), 403
    except ValueError as e:
        return jsonify(error="Bad Request", message=str(e)), 400

    return jsonify(message="Answer unaccepted."), 200
