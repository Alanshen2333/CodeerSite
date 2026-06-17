from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_current_user,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.schemas.auth import RegisterSchema, LoginSchema, UpdateProfileSchema
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def _get_user_or_401():
    """Get current user or return 401 if not found (e.g. deleted after token issue)."""
    user = get_current_user()
    if user is None:
        return None, (jsonify(error="Unauthorized", message="User not found."), 401)
    return user, None


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = RegisterSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    try:
        user = AuthService.register_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            display_name=data.get("display_name"),
        )
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Conflict", message="Username or email already taken."), 409
    except ValueError as e:
        return jsonify(error="Conflict", message=str(e)), 409

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        user=user.to_dict(),
        access_token=access_token,
        refresh_token=refresh_token,
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login and return tokens."""
    try:
        data = LoginSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user = AuthService.authenticate(email=data["email"], password=data["password"])
    if user is None:
        return jsonify(error="Unauthorized", message="Invalid email or password."), 401

    # Update last login
    try:
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        db.session.rollback()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        user=user.to_dict(),
        access_token=access_token,
        refresh_token=refresh_token,
    ), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user, error = _get_user_or_401()
    if error:
        return error
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get current user info."""
    user, error = _get_user_or_401()
    if error:
        return error
    return jsonify(user=user.to_dict()), 200


@auth_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    """Update current user profile."""
    try:
        data = UpdateProfileSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify(error="Validation Error", messages=e.messages), 422

    user, error = _get_user_or_401()
    if error:
        return error

    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(user=user.to_dict()), 200
