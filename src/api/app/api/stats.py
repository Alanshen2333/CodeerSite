from flask import Blueprint, jsonify
from app.models.question import Question
from app.models.answer import Answer
from app.models.project import Project
from app.models.user import User

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("", methods=["GET"])
def get_public_stats():
    """公开统计端点 — 首页统计卡片使用。"""
    return jsonify(
        questions=Question.query.count(),
        answers=Answer.query.count(),
        projects=Project.query.count(),
        users=User.query.count(),
    ), 200
