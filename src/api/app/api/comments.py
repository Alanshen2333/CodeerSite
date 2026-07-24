from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.comment import CommentCreateSchema, CommentUpdateSchema
from app.services.comment_service import CommentService

comments_bp = Blueprint("comments", __name__)


@comments_bp.route("", methods=["GET"])
def list_comments():
    """List comments for a target."""
    target_type = request.args.get("target_type")
    target_id = request.args.get("target_id")

    if not target_type or not target_id:
        return jsonify(
            error="Bad Request", message="target_type and target_id are required."
        ), 400

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = CommentService.get_comments(
        target_type, target_id, page=page, per_page=per_page
    )
    return jsonify(
        comments=[c.to_dict() for c in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@comments_bp.route("", methods=["POST"])
@jwt_required()
def create_comment():
    """Create a comment."""
    user = get_current_user()
    try:
        data = CommentCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    comment = CommentService.create_comment(
        user_id=user.id,
        body=data["body"],
        target_type=data["target_type"],
        target_id=data["target_id"],
    )
    return jsonify(comment=comment.to_dict()), 201


@comments_bp.route("/<comment_id>", methods=["PATCH"])
@jwt_required()
def update_comment(comment_id):
    """Update a comment. Only the author can update."""
    user = get_current_user()
    comment = CommentService.get_comment(comment_id)
    if not comment:
        return jsonify(error="Not Found", message="Comment not found."), 404
    if comment.user_id != user.id:
        return jsonify(
            error="Forbidden", message="You can only edit your own comments."
        ), 403

    try:
        data = CommentUpdateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    comment = CommentService.update_comment(comment, data["body"])
    return jsonify(comment=comment.to_dict()), 200


@comments_bp.route("/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment. Only the author or admin can delete."""
    user = get_current_user()
    comment = CommentService.get_comment(comment_id)
    if not comment:
        return jsonify(error="Not Found", message="Comment not found."), 404
    if comment.user_id != user.id and user.role not in ("moderator", "admin"):
        return jsonify(
            error="Forbidden", message="You can only delete your own comments."
        ), 403

    CommentService.delete_comment(comment)
    return jsonify(message="Comment deleted."), 200
