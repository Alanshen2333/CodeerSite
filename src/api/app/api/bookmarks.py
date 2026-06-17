from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.bookmark import BookmarkCreateSchema
from app.services.bookmark_service import BookmarkService

bookmarks_bp = Blueprint("bookmarks", __name__)


@bookmarks_bp.route("", methods=["GET"])
@jwt_required()
def list_bookmarks():
    """List current user's bookmarks."""
    user = get_current_user()
    target_type = request.args.get("target_type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = BookmarkService.get_user_bookmarks(
        user_id=user.id,
        target_type=target_type,
        page=page,
        per_page=per_page,
    )
    return jsonify(
        bookmarks=[b.to_dict() for b in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@bookmarks_bp.route("", methods=["POST"])
@jwt_required()
def toggle_bookmark():
    """Toggle a bookmark (create if not exists, delete if exists)."""
    user = get_current_user()
    try:
        data = BookmarkCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    bookmark, created = BookmarkService.toggle_bookmark(
        user_id=user.id,
        target_type=data["target_type"],
        target_id=data["target_id"],
    )
    if created:
        return jsonify(bookmark=bookmark.to_dict(), message="Bookmarked."), 201
    return jsonify(message="Bookmark removed."), 200


@bookmarks_bp.route("/check", methods=["GET"])
@jwt_required()
def check_bookmark():
    """Check if a target is bookmarked by current user."""
    user = get_current_user()
    target_type = request.args.get("target_type")
    target_id = request.args.get("target_id")

    if not target_type or not target_id:
        return jsonify(error="Bad Request", message="target_type and target_id are required."), 400

    bookmarked = BookmarkService.is_bookmarked(user.id, target_type, target_id)
    return jsonify(bookmarked=bookmarked), 200
