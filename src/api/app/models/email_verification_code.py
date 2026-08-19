import uuid
from datetime import datetime, timezone

from app.extensions import db


class EmailVerificationCode(db.Model):
    """邮箱验证码存储（PostgreSQL）。

    一个 email+purpose 只保留最新一条有效验证码：
    - sent_at 用于冷却期判断
    - expires_at 用于 TTL 失效
    - used 用于一次性消费（消费时通过原子 UPDATE 抢占，避免并发重复使用）
    """

    __tablename__ = "email_verification_codes"
    __table_args__ = (
        db.UniqueConstraint("email", "purpose", name="uq_email_code_purpose"),
        db.Index("ix_email_verification_codes_email_purpose", "email", "purpose"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def to_dict(self):
        return {
            "email": self.email,
            "purpose": self.purpose,
            "used": self.used,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
