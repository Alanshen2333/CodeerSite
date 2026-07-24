from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.schemas.vote import VoteCreateSchema
from app.services.vote_service import VoteService

votes_bp = Blueprint("votes", __name__)


@votes_bp.route("", methods=["POST"])
@jwt_required()
def vote():
    """Cast or change a vote."""
    user = get_current_user()
    try:
        data = VoteCreateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        VoteService.vote(
            user_id=user.id,
            vote_type=data["vote_type"],
            target_type=data["target_type"],
            target_id=data["target_id"],
        )
    except ValueError as e:
        msg = str(e)
        if "own content" in msg:
            return jsonify(error="Bad Request", message=msg), 400
        return jsonify(error="Not Found", message=msg), 404

    return jsonify(message="Vote recorded."), 200


@votes_bp.route("", methods=["DELETE"])
@jwt_required()
def remove_vote():
    """Remove a vote."""
    user = get_current_user()
    target_type = request.args.get("target_type")
    target_id = request.args.get("target_id")

    if not target_type or not target_id:
        return jsonify(
            error="Bad Request", message="target_type and target_id are required."
        ), 400

    try:
        VoteService.remove_vote(user.id, target_type, target_id)
    except ValueError as e:
        return jsonify(error="Not Found", message=str(e)), 404

    return jsonify(message="Vote removed."), 200
