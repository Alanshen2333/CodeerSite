import uuid
from datetime import datetime, timezone
from app.extensions import db


class Answer(db.Model):
    __tablename__ = "answers"
    __table_args__ = (
        db.CheckConstraint("vote_count >= 0", name="ck_answers_vote_count_nonnegative"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = db.Column(db.String(36), db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    vote_count = db.Column(db.Integer, default=0, nullable=False)
    is_accepted = db.Column(db.Boolean, default=False, nullable=False)
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
    author = db.relationship("User", backref="answers")

    def to_dict(self, include_body_html=True):
        data = {
            "id": self.id,
            "question_id": self.question_id,
            "author_id": self.author_id,
            "author": self.author.to_public_dict() if self.author else None,
            "body": self.body,
            "vote_count": self.vote_count,
            "is_accepted": self.is_accepted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_body_html:
            data["body_html"] = self.body_html
        return data

    def to_list_dict(self):
        return self.to_dict(include_body_html=False)
