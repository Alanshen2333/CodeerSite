import uuid
from datetime import datetime, timezone
from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"
    __table_args__ = (
        db.CheckConstraint(
            "star_count >= 0", name="ck_projects_star_count_nonnegative"
        ),
        db.CheckConstraint(
            "next_issue_number >= 1", name="ck_projects_next_issue_number_positive"
        ),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    visibility = db.Column(
        db.String(10), default="public", nullable=False
    )  # public/private
    star_count = db.Column(db.Integer, default=0, nullable=False)
    next_issue_number = db.Column(db.Integer, default=1, nullable=False)

    # Gitea (VCS backend) —— Project:Repo = 1:1 可选关联
    gitea_repo_id = db.Column(db.String(36), index=True, nullable=True)
    gitea_full_name = db.Column(db.String(255), nullable=True)

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
    members = db.relationship(
        "ProjectMember", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    issues = db.relationship(
        "Issue", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    milestones = db.relationship(
        "Milestone", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    kanban_columns = db.relationship(
        "KanbanColumn",
        backref="project",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="KanbanColumn.position",
    )

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
            "gitea_full_name": self.gitea_full_name,
            "has_repo": self.gitea_repo_id is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
