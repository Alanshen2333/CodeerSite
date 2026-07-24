from flask import Blueprint, jsonify, request, send_file, abort
from io import BytesIO
from app.extensions import db
from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer
from app.services.user_service import UserService
from app.services.badge_service import BadgeService

users_bp = Blueprint("users", __name__)


@users_bp.route("", methods=["GET"])
def list_users():
    """List users sorted by reputation. 支持 q 搜索 username/display_name。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)
    q = (request.args.get("q") or "").strip() or None

    users = UserService.get_users(page=page, per_page=per_page, q=q)
    return jsonify(
        users=[u.to_public_dict() for u in users.items],
        total=users.total,
        page=users.page,
        pages=users.pages,
    ), 200


@users_bp.route("/<username>", methods=["GET"])
def get_user(username):
    """Get user public profile."""
    user = UserService.get_user_by_username(username)
    if user is None:
        return jsonify(error="Not Found", message="User not found."), 404

    stats = UserService.get_user_stats(user.id)
    achievements = BadgeService.get_user_achievements(user)
    next_tier = BadgeService.get_next_tier(user)
    awarded_badges = BadgeService.get_user_awarded_badges(user.id)
    return jsonify(
        user=user.to_public_dict(),
        stats=stats,
        achievements=achievements,
        next_tier=next_tier,
        awarded_badges=[ub.to_dict() for ub in awarded_badges],
    ), 200


@users_bp.route("/<username>/questions", methods=["GET"])
def get_user_questions(username):
    """Get questions by a user."""
    user = UserService.get_user_by_username(username)
    if user is None:
        return jsonify(error="Not Found", message="User not found."), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = (
        Question.query.filter_by(author_id=user.id)
        .order_by(Question.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify(
        questions=[q.to_list_dict() for q in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@users_bp.route("/<username>/answers", methods=["GET"])
def get_user_answers(username):
    """Get answers by a user."""
    user = UserService.get_user_by_username(username)
    if user is None:
        return jsonify(error="Not Found", message="User not found."), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = (
        Answer.query.filter_by(author_id=user.id)
        .order_by(Answer.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify(
        answers=[a.to_dict() for a in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@users_bp.route("/<username>/badges", methods=["GET"])
def get_user_badges(username):
    """公开：获取用户已获的自定义徽章。"""
    user = UserService.get_user_by_username(username)
    if user is None:
        return jsonify(error="Not Found", message="User not found."), 404

    awarded = BadgeService.get_user_awarded_badges(user.id)
    return jsonify(badges=[ub.to_dict() for ub in awarded]), 200


@users_bp.route("/avatar/<user_id>", methods=["GET"])
def get_user_avatar(user_id):
    """公开：返回用户头像二进制。"""
    user = db.session.get(User, user_id)
    if user is None or not user.avatar_blob or not user.avatar_mime_type:
        abort(404)

    return send_file(
        BytesIO(user.avatar_blob),
        mimetype=user.avatar_mime_type,
        max_age=86400,
    ), 200
