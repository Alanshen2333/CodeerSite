from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.tag import Tag
from app.schemas.tag import TagCreateSchema
from app.services.tag_service import TagService

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("", methods=["GET"])
def list_tags():
    """List tags sorted by popularity or name."""
    sort = request.args.get("sort", "popular")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 36, type=int)
    per_page = min(per_page, 100)

    search = request.args.get("q")
    if search:
        tags = TagService.search_tags(search, limit=per_page)
        return jsonify(tags=[t.to_dict() for t in tags]), 200

    result = TagService.get_tags(sort=sort, page=page, per_page=per_page)
    return jsonify(
        tags=[t.to_dict() for t in result.items],
        total=result.total,
        page=result.page,
        pages=result.pages,
    ), 200


@tags_bp.route("/<slug>", methods=["GET"])
def get_tag(slug):
    """Get a single tag by slug."""
    tag = TagService.get_tag_by_slug(slug)
    if not tag:
        return jsonify(error="Not Found", message="Tag not found."), 404
    return jsonify(tag=tag.to_dict()), 200


@tags_bp.route("", methods=["POST"])
@jwt_required()
def create_tag():
    """Create a new tag (authenticated users)."""
    try:
        data = TagCreateSchema().load(request.get_json())
    except Exception as e:
        return jsonify(error="Validation Error", messages=str(e)), 422

    # Check if tag already exists
    existing = Tag.query.filter_by(name=data["name"].strip().lower()).first()
    if existing:
        return jsonify(error="Conflict", message="Tag already exists."), 409

    # Create tag
    slug = TagService._slugify(data["name"].strip().lower())
    tag = Tag(
        name=data["name"].strip().lower(),
        slug=slug,
        description=data.get("description"),
        color=data.get("color", "#1677ff"),
    )
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag=tag.to_dict()), 201
