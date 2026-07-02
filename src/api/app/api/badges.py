from flask import Blueprint, jsonify
from app.services.badge_service import BadgeService

badges_bp = Blueprint("badges", __name__)


@badges_bp.route("", methods=["GET"])
def list_badges():
    """公开：列出所有自定义徽章定义。"""
    badges = BadgeService.list_badges()
    return jsonify(badges=[b.to_dict() for b in badges]), 200


@badges_bp.route("/<slug>", methods=["GET"])
def get_badge(slug):
    """公开：按 slug 获取单个徽章定义。"""
    badge = BadgeService.get_badge_by_slug(slug)
    if not badge:
        return jsonify(error="Not Found", message="Badge not found."), 404
    return jsonify(badge=badge.to_dict()), 200
