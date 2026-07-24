import uuid
from datetime import datetime, timezone
from app.extensions import db

# Many-to-many association table for issue <-> tag
issue_tags = db.Table(
    "issue_tags",
    db.Column(
        "issue_id",
        db.String(36),
        db.ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.String(36),
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Issue(db.Model):
    """项目内 Issue。

    时间跟踪字段单位均为**秒**（Integer）：
    - time_estimate：预估工时（可由创建者/成员设置，可为空表示未估时）
    - time_spent：已耗时，反范式缓存的累计值（由 time_entries 聚合维护，读多写少）
    """

    __tablename__ = "issues"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(
        db.String(36),
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_number = db.Column(
        db.Integer, nullable=False
    )  # Auto-increment within project
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    author_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    assignee_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True, index=True
    )
    status = db.Column(
        db.String(20), default="open", nullable=False
    )  # open/in_progress/closed
    priority = db.Column(
        db.String(10), default="medium", nullable=False
    )  # low/medium/high/critical
    milestone_id = db.Column(
        db.String(36),
        db.ForeignKey("milestones.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 时间跟踪：单位秒。time_estimate 可空；time_spent 默认 0，由 time_entries 聚合反范式维护。
    time_estimate = db.Column(db.Integer, nullable=True)  # 预估工时（秒）
    time_spent = db.Column(
        db.Integer, default=0, nullable=False
    )  # 已耗时（秒，聚合缓存）
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
        db.UniqueConstraint(
            "project_id", "issue_number", name="uq_project_issue_number"
        ),
    )

    author = db.relationship(
        "User", foreign_keys=[author_id], backref="authored_issues"
    )
    assignee = db.relationship(
        "User", foreign_keys=[assignee_id], backref="assigned_issues"
    )
    milestone = db.relationship("Milestone", backref="issues")
    tags = db.relationship("Tag", secondary=issue_tags, backref="issues", lazy="joined")
    time_entries = db.relationship(
        "TimeEntry",
        backref="issue",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self, include_time_entries: bool = False):
        data = {
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
            "tags": [t.to_dict() for t in self.tags] if self.tags else [],
            "time_estimate": self.time_estimate,
            "time_spent": self.time_spent or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_time_entries:
            data["time_entries"] = (
                [e.to_dict() for e in self.time_entries] if self.time_entries else []
            )
        return data


class TimeEntry(db.Model):
    """Issue 耗时记录条目 —— 支持多次累计，Issue.time_spent 为其聚合反范式缓存。

    seconds 为本次记录的耗时（秒，正整数）。
    """

    __tablename__ = "time_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = db.Column(
        db.String(36),
        db.ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    seconds = db.Column(db.Integer, nullable=False)  # 本次耗时（秒）
    note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", backref="time_entries")

    def to_dict(self):
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "user_id": self.user_id,
            "user": self.user.to_public_dict() if self.user else None,
            "seconds": self.seconds,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
