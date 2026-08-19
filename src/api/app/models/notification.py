import uuid
from datetime import datetime, timezone

from app.extensions import db


class Notification(db.Model):
    """站内通知（PostgreSQL）。

    替代早期 MongoDB notifications 集合，响应结构与旧实现保持一致。
    过期数据由 NotificationService.delete_expired() 按 90 天策略清理。
    """

    __tablename__ = "notifications"
    __table_args__ = (
        db.Index(
            "ix_notifications_recipient_created",
            "recipient_id",
            "created_at",
        ),
        db.Index(
            "ix_notifications_recipient_read",
            "recipient_id",
            "is_read",
        ),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True)
    source_type = db.Column(db.String(20), nullable=True)
    source_id = db.Column(db.String(36), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "link": self.link,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
