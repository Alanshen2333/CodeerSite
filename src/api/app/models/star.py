import uuid
from datetime import datetime, timezone
from app.extensions import db


class Star(db.Model):
    """用户对项目的 star（点赞/关注，带公开计数）。

    与 bookmark（私人收藏）不同：star 影响项目排序与公开 star_count，
    故用独立表 + FK，便于可靠维护反范式 star_count 缓存。
    """

    __tablename__ = "project_stars"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    project_id = db.Column(
        db.String(36), db.ForeignKey("projects.id"), nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "project_id", name="uq_user_project_star"),
    )

    user = db.relationship("User", backref="stars")
    project = db.relationship("Project", backref="stars")
