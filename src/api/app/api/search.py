from flask import Blueprint, request, jsonify
from app.services.search_service import SearchService

search_bp = Blueprint("search", __name__)


@search_bp.route("", methods=["GET"])
def search():
    """Global full-text search across questions, answers, issues, and projects."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Validation Error", message="Query parameter 'q' is required."), 400

    source_type = request.args.get("type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 50)

    result = SearchService.search(q=q, source_type=source_type, page=page, per_page=per_page)
    return jsonify(**result), 200
