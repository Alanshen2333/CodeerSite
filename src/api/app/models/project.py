import uuid
from datetime import datetime, timezone
from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    visibility = db.Column(db.String(10), default="public", nullable=False)  # public/private
    star_count = db.Column(db.Integer, default=0, nullable=False)
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

    owner = db.relationship("User", backref="owned_projects")
    members = db.relationship("ProjectMember", backref="project", lazy="dynamic", cascade="all, delete-orphan")
    issues = db.relationship("Issue", backref="project", lazy="dynamic", cascade="all, delete-orphan")
    milestones = db.relationship("Milestone", backref="project", lazy="dynamic", cascade="all, delete-orphan")
    kanban_columns = db.relationship("KanbanColumn", backref="project", lazy="dynamic",
                                     cascade="all, delete-orphan", order_by="KanbanColumn.position")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "owner_id": self.owner_id,
            "owner": self.owner.to_public_dict() if self.owner else None,
            "visibility": self.visibility,
            "star_count": self.star_count,
            "members_count": self.members.count(),
            "issues_count": self.issues.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
