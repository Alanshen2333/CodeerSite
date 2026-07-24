import uuid
from datetime import datetime, timezone
from app.extensions import db


class KanbanCard(db.Model):
    __tablename__ = "kanban_cards"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    column_id = db.Column(
        db.String(36),
        db.ForeignKey("kanban_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_id = db.Column(
        db.String(36), db.ForeignKey("issues.id", ondelete="CASCADE"), nullable=True
    )
    title = db.Column(db.String(200), nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    issue = db.relationship("Issue", backref="kanban_card")

    def to_dict(self):
        return {
            "id": self.id,
            "column_id": self.column_id,
            "issue_id": self.issue_id,
            "issue": self.issue.to_dict() if self.issue else None,
            "title": self.title,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
