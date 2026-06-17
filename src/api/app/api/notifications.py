from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    """List notifications for current user."""
    user = get_current_user()
    unread_only = request.args.get("unread", "").lower() == "true"
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = NotificationService.list_for_user(
        user_id=user.id,
        unread_only=unread_only,
        page=page,
        per_page=per_page,
    )
    return jsonify(**result), 200


@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    """Get unread notification count for current user."""
    user = get_current_user()
    count = NotificationService.unread_count(user.id)
    return jsonify(unread_count=count), 200


@notifications_bp.route("/<notification_id>/read", methods=["PATCH"])
@jwt_required()
def mark_read(notification_id):
    """Mark a single notification as read."""
    user = get_current_user()
    ok = NotificationService.mark_read(notification_id, user.id)
    if not ok:
        return jsonify(error="Not Found", message="Notification not found."), 404
    return jsonify(message="Marked as read."), 200


@notifications_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_read():
    """Mark all notifications as read for current user."""
    user = get_current_user()
    count = NotificationService.mark_all_read(user.id)
    return jsonify(message=f"{count} notifications marked as read."), 200
