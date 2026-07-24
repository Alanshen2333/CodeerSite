import uuid
from datetime import datetime, timezone
from app.extensions import db


class Bookmark(db.Model):
    """Polymorphic bookmark: target_type = 'question' | 'project'."""

    __tablename__ = "bookmarks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "target_type", "target_id", name="uq_user_target_bookmark"
        ),
    )

    user = db.relationship("User", backref="bookmarks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
