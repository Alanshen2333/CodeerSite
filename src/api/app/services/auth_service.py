from app.extensions import db
from app.models.user import User
from app.services.email_code_service import EmailCodeService
from app.services.gitea_client import GiteaClient
from app.utils.crypto import encrypt_token


class AuthService:
    @staticmethod
    def register_user(username: str, email: str, password: str, display_name: str = None) -> User:
        """Register a new user. Raises ValueError on duplicate.

        Gitea 用户同步创建；失败不影响 Codeersite 注册成功，仅记录 warning。
        """
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already taken.")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered.")

        user = User(
            username=username,
            email=email.lower(),
            display_name=display_name or username,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Gitea 认证桥接：用户注册成功后同步创建 Gitea 用户并缓存 token
        if GiteaClient._is_available():
            gitea_user = GiteaClient.admin_create_user(
                username=username,
                email=user.email,
                password=password,
            )
            if gitea_user:
                user.gitea_user_id = str(gitea_user.get("id"))
                token = GiteaClient.admin_create_user_token(username)
                if token:
                    user.gitea_token_encrypted = encrypt_token(token)
                db.session.commit()

        return user

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        """Authenticate user by email and password. Returns None on failure."""
        user = User.query.filter_by(email=email.lower()).first()
        if user is None:
            return None
        if not user.is_active:
            return None
        if not user.check_password(password):
            return None
        return user

    @staticmethod
    def change_password(user: User, verification_code: str, new_password: str) -> User:
        """校验邮箱验证码后修改密码。"""
        if not EmailCodeService.verify_code(user.email, "change_password", verification_code):
            raise ValueError("验证码无效或已过期。")
        user.set_password(new_password)
        db.session.commit()
        return user
