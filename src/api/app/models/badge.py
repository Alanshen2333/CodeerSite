import uuid
from datetime import datetime, timezone
from app.extensions import db


class Badge(db.Model):
    """徽章定义：管理员可创建/编辑的自定义徽章。

    kind 取值：
    - tier        声望等级（保留，由 BadgeService.BADGE_TIERS 计算，不入库）
    - achievement 成就（保留，由 BadgeService.ACHIEVEMENTS 计算，不入库）
    - custom      自定义徽章（管理员手动创建 + 发放）
    """

    __tablename__ = "badges"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(20), nullable=True)
    color = db.Column(db.String(7), default="#5e6ad2", nullable=False)
    kind = db.Column(db.String(20), default="custom", nullable=False)
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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "kind": self.kind,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserBadge(db.Model):
    """用户已获徽章（管理员发放关系）。"""

    __tablename__ = "user_badges"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    badge_id = db.Column(db.String(36), db.ForeignKey("badges.id"), nullable=False, index=True)
    awarded_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    badge = db.relationship("Badge", lazy="joined")
    user = db.relationship("User", foreign_keys=[user_id], backref="user_badges")
    awarder = db.relationship("User", foreign_keys=[awarded_by])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "badge_id": self.badge_id,
            "badge": self.badge.to_dict() if self.badge else None,
            "awarded_by": self.awarded_by,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
