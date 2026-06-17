import uuid
from datetime import datetime, timezone
from app.extensions import db


class KanbanColumn(db.Model):
    __tablename__ = "kanban_columns"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cards = db.relationship("KanbanCard", backref="column", lazy="dynamic",
                            cascade="all, delete-orphan", order_by="KanbanCard.position")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
