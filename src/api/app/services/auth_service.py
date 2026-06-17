from app.extensions import db
from app.models.user import User


class AuthService:
    @staticmethod
    def register_user(username: str, email: str, password: str, display_name: str = None) -> User:
        """Register a new user. Raises ValueError on duplicate."""
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
