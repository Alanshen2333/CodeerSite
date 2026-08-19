import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete, update
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """PostgreSQL-backed notification system.

    响应结构与早期 MongoDB 实现保持兼容；过期通知通过 delete_expired()
    按 90 天策略清理（可由 scripts/purge_notifications.py 定时调用）。
    """

    TTL_SECONDS = 90 * 24 * 3600

    @classmethod
    def create(
        cls,
        recipient_id: str,
        type_: str,
        title: str,
        body: str | None = None,
        link: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
    ) -> dict:
        try:
            notification = Notification(
                recipient_id=recipient_id,
                type=type_,
                title=title,
                body=body,
                link=link,
                source_type=source_type,
                source_id=source_id,
            )
            db.session.add(notification)
            db.session.commit()
            return notification.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.warning("Failed to create notification for user %s", recipient_id, exc_info=True)
            return {}

    @classmethod
    def list_for_user(
        cls, user_id: str, unread_only: bool = False, page: int = 1, per_page: int = 20
    ) -> dict:
        page = max(page, 1)
        per_page = min(max(per_page, 1), 50)
        query = Notification.query.filter_by(recipient_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        total = query.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = (
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return {
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "pages": pages,
        }

    @classmethod
    def mark_read(cls, notification_id: str, user_id: str) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount > 0

    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount

    @classmethod
    def unread_count(cls, user_id: str) -> int:
        return (
            Notification.query.filter_by(recipient_id=user_id, is_read=False).count()
        )

    @classmethod
    def delete_expired(cls, ttl_seconds: int | None = None) -> int:
        """删除超过保留期的通知，返回删除条数。"""
        ttl_seconds = ttl_seconds or cls.TTL_SECONDS
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        stmt = delete(Notification).where(Notification.created_at < cutoff)
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount
