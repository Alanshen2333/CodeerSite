import uuid
from datetime import datetime, timezone
from app.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    avatar_blob = db.Column(db.LargeBinary, nullable=True)
    avatar_mime_type = db.Column(db.String(32), nullable=True)
    avatar_updated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    reputation = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    email_verified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Gitea (VCS backend) —— token 加密存储，永不返回前端
    gitea_user_id = db.Column(db.String(36), index=True, nullable=True)
    gitea_token_encrypted = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships (lazy-loaded, added later as models are built)
    # questions = db.relationship("Question", backref="author", lazy="dynamic")
    # answers = db.relationship("Answer", backref="author", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_avatar_url(self):
        """返回指向头像 API 的动态 URL；若未上传过头像则回退 avatar_url 字段。"""
        if self.avatar_blob and self.avatar_mime_type:
            ts = ""
            if self.avatar_updated_at:
                ts = f"?t={self.avatar_updated_at.timestamp()}"
            return f"/api/users/avatar/{self.id}{ts}"
        return self.avatar_url

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.get_avatar_url(),
            "bio": self.bio,
            "website": self.website,
            "location": self.location,
            "reputation": self.reputation,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_public_dict(self):
        """Return public-safe user data (no email/password)."""
        from app.services.badge_service import BadgeService
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.get_avatar_url(),
            "bio": self.bio,
            "website": self.website,
            "location": self.location,
            "reputation": self.reputation,
            "role": self.role,
            "badge": BadgeService.get_user_badge(self),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
