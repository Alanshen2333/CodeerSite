import os


import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://codeersite:codeersite_dev@localhost:5432/codeersite",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/codeersite")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-key-change-me-to-32-bytes-min")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        """Production safeguards."""
        secret = app.config.get("SECRET_KEY", "")
        jwt_secret = app.config.get("JWT_SECRET_KEY", "")
        if "change-me" in secret or "change-me" in jwt_secret:
            raise RuntimeError(
                "SECRET_KEY and JWT_SECRET_KEY must be set via environment "
                "variables in production. Do not use the dev defaults."
            )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MONGO_URI = "mongodb://localhost:27017/codeersite_test"
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 100


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig,
    "default": ProductionConfig,
}
