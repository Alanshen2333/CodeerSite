from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer
from app.models.project import Project
from app.schemas.badge import (
    BadgeCreateSchema,
    BadgeUpdateSchema,
    AwardSchema,
    RevokeSchema,
)
from app.services.badge_service import BadgeService
from app.schemas.auth import AdminUserUpdateSchema
from app.extensions import db

admin_bp = Blueprint("admin", __name__)


def _require_admin():
    user = get_current_user()
    if user is None:
        return None, (
            jsonify(error="Unauthorized", message="Authentication required."),
            401,
        )
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

    try:
        data = AdminUserUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    if data.get("role") is not None:
        user.role = data["role"]
    if data.get("is_active") is not None:
        user.is_active = data["is_active"]

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


# ── 徽章管理 ─────────────────────────────────────────────


@admin_bp.route("/badges", methods=["GET"])
@jwt_required()
def list_badges():
    """Admin: 列出所有自定义徽章定义。"""
    _, err = _require_admin()
    if err:
        return err
    badges = BadgeService.list_badges()
    return jsonify(badges=[b.to_dict() for b in badges]), 200


@admin_bp.route("/badges", methods=["POST"])
@jwt_required()
def create_badge():
    """Admin: 创建徽章定义。"""
    admin_user, err = _require_admin()
    if err:
        return err
    try:
        data = BadgeCreateSchema().load(request.get_json() or {})
    except Exception as e:
        return jsonify(error="Validation Error", messages=str(e)), 422

    try:
        badge = BadgeService.create_badge(
            name=data["name"],
            description=data.get("description"),
            icon=data.get("icon"),
            color=data.get("color", "#5e6ad2"),
        )
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    db.session.commit()
    return jsonify(badge=badge.to_dict()), 201


@admin_bp.route("/badges/<badge_id>", methods=["PATCH"])
@jwt_required()
def update_badge(badge_id):
    """Admin: 更新徽章定义。"""
    _, err = _require_admin()
    if err:
        return err
    badge = BadgeService.get_badge(badge_id)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404

    try:
        data = BadgeUpdateSchema().load(request.get_json() or {}, partial=True)
    except Exception as e:
        return jsonify(error="Validation Error", messages=str(e)), 422

    try:
        badge = BadgeService.update_badge(badge, data)
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    db.session.commit()
    return jsonify(badge=badge.to_dict()), 200


@admin_bp.route("/badges/<badge_id>", methods=["DELETE"])
@jwt_required()
def delete_badge(badge_id):
    """Admin: 删除徽章定义（连同发放关系）。"""
    _, err = _require_admin()
    if err:
        return err
    badge = BadgeService.get_badge(badge_id)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404

    BadgeService.delete_badge(badge)
    db.session.commit()
    return jsonify(message="Badge deleted."), 200


@admin_bp.route("/badges/<badge_id>/recipients", methods=["GET"])
@jwt_required()
def list_recipients(badge_id):
    """Admin: 查看某徽章的所有获得者。"""
    _, err = _require_admin()
    if err:
        return err
    badge = BadgeService.get_badge(badge_id)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404

    recipients = BadgeService.get_recipients(badge)
    return jsonify(recipients=[r.to_dict() for r in recipients]), 200


@admin_bp.route("/badges/<badge_id>/award", methods=["POST"])
@jwt_required()
def award_badge(badge_id):
    """Admin: 向用户发放徽章。"""
    admin_user, err = _require_admin()
    if err:
        return err
    badge = BadgeService.get_badge(badge_id)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404

    try:
        data = AwardSchema().load(request.get_json() or {})
    except Exception as e:
        return jsonify(error="Validation Error", messages=str(e)), 422

    try:
        ub = BadgeService.award(
            badge,
            data["user_id"],
            awarded_by=admin_user.id,
            reason=data.get("reason"),
        )
    except LookupError as e:
        return jsonify(error="Not Found", message=str(e)), 404
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    db.session.commit()
    return jsonify(award=ub.to_dict()), 201


@admin_bp.route("/badges/<badge_id>/award", methods=["DELETE"])
@jwt_required()
def revoke_badge(badge_id):
    """Admin: 撤销用户徽章。body: {user_id}。"""
    _, err = _require_admin()
    if err:
        return err
    badge = BadgeService.get_badge(badge_id)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404

    try:
        data = RevokeSchema().load(request.get_json() or {})
    except Exception as e:
        return jsonify(error="Validation Error", messages=str(e)), 422

    try:
        BadgeService.revoke(badge, data["user_id"])
    except LookupError as e:
        return jsonify(error="Not Found", message=str(e)), 404

    db.session.commit()
    return jsonify(message="Badge revoked."), 200
