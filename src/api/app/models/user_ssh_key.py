import uuid
from datetime import datetime, timezone
from app.extensions import db


class UserSshKey(db.Model):
    __tablename__ = "user_ssh_keys"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(100), nullable=False)
    key_type = db.Column(
        db.String(50), nullable=False
    )  # ssh-rsa / ssh-ed25519 / ecdsa-sha2-nistp256 等
    key_data = db.Column(db.Text, nullable=False)  # base64 编码的公钥主体
    fingerprint = db.Column(db.String(64), nullable=False, index=True, unique=True)
    gitea_key_id = db.Column(db.String(36), nullable=True)
    sync_status = db.Column(
        db.String(10), default="pending", nullable=False
    )  # pending/synced/failed
    sync_error = db.Column(db.Text, nullable=True)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    user = db.relationship(
        "User",
        backref=db.backref("ssh_keys", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "key_type": self.key_type,
            "fingerprint": self.fingerprint,
            "gitea_key_id": self.gitea_key_id,
            "sync_status": self.sync_status,
            "sync_error": self.sync_error,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
