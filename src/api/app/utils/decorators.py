from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_current_user


def admin_required(fn):
    """Decorator that checks if the current user is an admin."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None or user.role != "admin":
            return jsonify(error="Forbidden", message="Admin access required."), 403
        return fn(*args, **kwargs)

    return wrapper


def moderator_required(fn):
    """Decorator that checks if the current user is a moderator or admin."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None or user.role not in ("moderator", "admin"):
            return jsonify(error="Forbidden", message="Moderator access required."), 403
        return fn(*args, **kwargs)

    return wrapper
