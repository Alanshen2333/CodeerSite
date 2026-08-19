from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()


def init_extensions(app):
    """Initialize all Flask extensions."""
    db.init_app(app)
    jwt.init_app(app)

    # CORS: use configured origins, not wildcard
    origins = app.config.get("CORS_ORIGINS", "http://localhost:3000")
    cors.init_app(app, resources={r"/api/*": {"origins": origins.split(",")}})

    bcrypt.init_app(app)


@jwt.token_in_blocklist_loader
def token_blocklist_callback(_jwt_header, jwt_data):
    """Check if token has been revoked. Returns True if revoked.

    查询 PostgreSQL 的 jwt_blocklist 表；查询异常时 fail-closed（视为已吊销），
    避免早期 MongoDB 不可用时 fail-open 导致吊销失效。
    """
    jti = jwt_data.get("jti")
    if jti is None:
        return False

    from app.models.jwt_blocklist import JWTBlocklist

    try:
        return db.session.get(JWTBlocklist, jti) is not None
    except Exception:  # pragma: no cover - defensive fail-closed path
        return True


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Register callback to load user object from JWT identity (user ID string)."""
    from app.models.user import User

    user_id = jwt_data.get("sub")
    if user_id is None:
        return None
    return db.session.get(User, user_id)
