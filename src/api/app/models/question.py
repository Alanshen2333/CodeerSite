import uuid
from datetime import datetime, timezone
from app.extensions import db

# Many-to-many association table for question <-> tag
question_tags = db.Table(
    "question_tags",
    db.Column("question_id", db.String(36), db.ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.String(36), db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Question(db.Model):
    __tablename__ = "questions"
    __table_args__ = (
        db.CheckConstraint("vote_count >= 0", name="ck_questions_vote_count_nonnegative"),
        db.CheckConstraint("answer_count >= 0", name="ck_questions_answer_count_nonnegative"),
        db.CheckConstraint("view_count >= 0", name="ck_questions_view_count_nonnegative"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    vote_count = db.Column(db.Integer, default=0, nullable=False)
    answer_count = db.Column(db.Integer, default=0, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    accepted_answer_id = db.Column(db.String(36), nullable=True)
    is_closed = db.Column(db.Boolean, default=False, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
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

    # Relationships
    author = db.relationship("User", backref="questions")
    tags = db.relationship("Tag", secondary=question_tags, backref="questions", lazy="joined")
    answers = db.relationship("Answer", backref="question", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_body_html=True):
        data = {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "author_id": self.author_id,
            "author": self.author.to_public_dict() if self.author else None,
            "tags": [t.to_dict() for t in self.tags] if self.tags else [],
            "vote_count": self.vote_count,
            "answer_count": self.answer_count,
            "view_count": self.view_count,
            "accepted_answer_id": self.accepted_answer_id,
            "is_closed": self.is_closed,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_body_html:
            data["body_html"] = self.body_html
        return data

    def to_list_dict(self):
        """Compact representation for list views (no body_html for bandwidth)."""
        return self.to_dict(include_body_html=False)
