from datetime import datetime, timezone

from app.extensions import db


class JWTBlocklist(db.Model):
    """JWT 吊销表（PostgreSQL）。

    表里存在对应 jti 即视为已吊销。token_in_blocklist_loader 查询本表；
    查询失败时 fail-closed（视为已吊销），避免早期 MongoDB 不可用时的 fail-open。
    """

    __tablename__ = "jwt_blocklist"

    jti = db.Column(db.String(36), primary_key=True)
    token_type = db.Column(db.String(20), nullable=False)  # access | refresh
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "jti": self.jti,
            "token_type": self.token_type,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }
