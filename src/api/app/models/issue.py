import uuid
from datetime import datetime, timezone
from app.extensions import db


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_number = db.Column(db.Integer, nullable=False)  # Auto-increment within project
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    author_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    assignee_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    status = db.Column(db.String(20), default="open", nullable=False)  # open/in_progress/closed
    priority = db.Column(db.String(10), default="medium", nullable=False)  # low/medium/high/critical
    milestone_id = db.Column(db.String(36), db.ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True)
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

    __table_args__ = (
        db.UniqueConstraint("project_id", "issue_number", name="uq_project_issue_number"),
    )

    author = db.relationship("User", foreign_keys=[author_id], backref="authored_issues")
    assignee = db.relationship("User", foreign_keys=[assignee_id], backref="assigned_issues")
    milestone = db.relationship("Milestone", backref="issues")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "issue_number": self.issue_number,
            "title": self.title,
            "body": self.body,
            "body_html": self.body_html,
            "author_id": self.author_id,
            "author": self.author.to_public_dict() if self.author else None,
            "assignee_id": self.assignee_id,
            "assignee": self.assignee.to_public_dict() if self.assignee else None,
            "status": self.status,
            "priority": self.priority,
            "milestone_id": self.milestone_id,
            "milestone": self.milestone.to_dict() if self.milestone else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
