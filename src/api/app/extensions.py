from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from pymongo import MongoClient

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()
mongo_client: MongoClient | None = None
mongo_db = None


def init_extensions(app):
    """Initialize all Flask extensions."""
    global mongo_client, mongo_db

    db.init_app(app)
    jwt.init_app(app)

    # CORS: use configured origins, not wildcard
    origins = app.config.get("CORS_ORIGINS", "http://localhost:3000")
    cors.init_app(app, resources={r"/api/*": {"origins": origins.split(",")}})

    bcrypt.init_app(app)

    # MongoDB with lazy connect to avoid startup crash when unavailable
    mongo_timeout = app.config.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000)
    try:
        mongo_client = MongoClient(
            app.config["MONGO_URI"],
            connect=False,
            serverSelectionTimeoutMS=mongo_timeout,
        )
        mongo_db = mongo_client.get_default_database()
        # Test connection with short timeout, ignore if unavailable
        if app.config.get("TESTING"):
            mongo_client.admin.command("ping")
    except Exception as e:
        app.logger.warning("MongoDB connection failed: %s", e)
        mongo_client = None
        mongo_db = None


def close_mongo():
    """Close MongoDB connection on app teardown."""
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None


@jwt.token_in_blocklist_loader
def token_blocklist_callback(_jwt_header, jwt_data):
    """Check if token has been revoked. Returns True if revoked."""
    jti = jwt_data.get("jti")
    if jti is None:
        return False
    db_mongo = get_mongo_db()
    if db_mongo is None:
        return False
    return db_mongo.blocklisted_tokens.find_one({"jti": jti}) is not None


def get_mongo_db():
    """Return the MongoDB database instance."""
    return mongo_db


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Register callback to load user object from JWT identity (user ID string)."""
    from app.models.user import User

    user_id = jwt_data.get("sub")
    if user_id is None:
        return None
    return db.session.get(User, user_id)
