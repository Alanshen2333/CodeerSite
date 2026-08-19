import os


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://codeersite:codeersite_dev@localhost:5432/codeersite",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "jwt-dev-secret-key-change-me-to-32-bytes-min"
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Gitea (VCS backend)
    GITEA_URL = os.getenv("GITEA_URL", "")
    # 浏览器可访问的 Gitea 地址；容器部署时与内部 GITEA_URL 分离。
    GITEA_PUBLIC_URL = os.getenv("GITEA_PUBLIC_URL", GITEA_URL)
    GITEA_ADMIN_TOKEN = os.getenv("GITEA_ADMIN_TOKEN", "")
    GITEA_ADMIN_USER = os.getenv("GITEA_ADMIN_USER", "")
    GITEA_ADMIN_PASS = os.getenv("GITEA_ADMIN_PASS", "")
    GITEA_ORG = os.getenv("GITEA_ORG", "codeersite")
    GITEA_TOKEN_ENCRYPTION_KEY = os.getenv("GITEA_TOKEN_ENCRYPTION_KEY", "")
    # 公开项目匿名读取仓库内容时使用的 token；未配置则回退到 ADMIN_TOKEN
    GITEA_PUBLIC_READONLY_TOKEN = os.getenv("GITEA_PUBLIC_READONLY_TOKEN", "")

    # Gitea OAuth2 application（在 Gitea 管理后台 → Applications 创建）
    GITEA_OAUTH_CLIENT_ID = os.getenv("GITEA_OAUTH_CLIENT_ID", "")
    GITEA_OAUTH_CLIENT_SECRET = os.getenv("GITEA_OAUTH_CLIENT_SECRET", "")
    GITEA_OAUTH_REDIRECT_URI = os.getenv(
        "GITEA_OAUTH_REDIRECT_URI",
        "http://localhost:3000/oauth/gitea",
    )

    # 头像上传
    MAX_AVATAR_SIZE = int(os.getenv("MAX_AVATAR_SIZE", "2097152"))

    # 邮箱验证码
    EMAIL_CODE_TTL = int(os.getenv("EMAIL_CODE_TTL", "300"))
    MAIL_DRIVER = os.getenv("MAIL_DRIVER", "console")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@codeer.site")


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
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://codeersite:codeersite_dev@localhost:5432/codeersite_test",
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 30,
        "pool_pre_ping": True,
    }
    # 测试环境关闭 Gitea 桥接，但保留合法 Fernet key 以便测试加解密
    GITEA_URL = ""
    GITEA_PUBLIC_URL = ""
    GITEA_ADMIN_TOKEN = ""
    GITEA_ADMIN_USER = ""
    GITEA_ADMIN_PASS = ""
    # 32 字节全 0 的 base64，仅用于测试，切勿用于生产
    GITEA_TOKEN_ENCRYPTION_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    GITEA_PUBLIC_READONLY_TOKEN = ""


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig,
    "default": ProductionConfig,
}
