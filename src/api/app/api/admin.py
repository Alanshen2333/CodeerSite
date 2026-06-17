from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer
from app.models.project import Project
from app.extensions import db

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    user = get_current_user()
    if user is None:
        return None, (jsonify(error="Unauthorized", message="Authentication required."), 401)
    if user.role != "admin":
        return None, (jsonify(error="Forbidden", message="Admin access required."), 403)
    return user, None


@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """Get site-wide statistics."""
    _, err = _require_admin()
    if err:
        return err

    return jsonify(
        users=User.query.count(),
        active_users=User.query.filter_by(is_active=True).count(),
        questions=Question.query.count(),
        answers=Answer.query.count(),
        projects=Project.query.count(),
        admins=User.query.filter_by(role="admin").count(),
        moderators=User.query.filter_by(role="moderator").count(),
    ), 200


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """Admin: list all users with full details."""
    _, err = _require_admin()
    if err:
        return err

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = User.query.order_by(User.created_at.desc())
    result = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        users=[u.to_dict() for u in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@admin_bp.route("/users/<user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    """Admin: update user role or ban status."""
    _, err = _require_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify(error="Not Found", message="User not found."), 404

    data = request.get_json() or {}
    if "role" in data and data["role"] in ("user", "moderator", "admin"):
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(user=user.to_dict()), 200


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """Admin: delete a user."""
    admin_user, err = _require_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify(error="Not Found", message="User not found."), 404
    if user.id == admin_user.id:
        return jsonify(error="Forbidden", message="Cannot delete yourself."), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify(message="User deleted."), 200
