import uuid
from datetime import datetime, timezone
from app.extensions import get_mongo_db


class NotificationService:
    """MongoDB-backed notification system with TTL auto-cleanup."""

    COLLECTION = "notifications"
    TTL_SECONDS = 90 * 24 * 3600  # 90 days

    @classmethod
    def _collection(cls):
        db = get_mongo_db()
        if db is None:
            return None
        return db[cls.COLLECTION]

    @classmethod
    def _ensure_indexes(cls):
        col = cls._collection()
        if col is None:
            return
        col.create_index(
            [("recipient_id", 1), ("is_read", 1), ("created_at", -1)],
            name="notif_recipient_idx",
        )
        col.create_index(
            "created_at",
            expireAfterSeconds=cls.TTL_SECONDS,
            name="notif_ttl_idx",
        )

    @classmethod
    def create(cls, recipient_id: str, type_: str, title: str,
               body: str | None = None, link: str | None = None,
               source_type: str | None = None, source_id: str | None = None) -> dict:
        """Create a notification and return it as a dict."""
        col = cls._collection()
        if col is None:
            return {}
        now = datetime.now(timezone.utc)
        doc = {
            "_id": str(uuid.uuid4()),
            "recipient_id": recipient_id,
            "type": type_,
            "title": title,
            "body": body,
            "link": link,
            "source_type": source_type,
            "source_id": source_id,
            "is_read": False,
            "created_at": now,
        }
        col.insert_one(doc)
        doc.pop("_id", None)
        return cls._format(doc)

    @classmethod
    def list_for_user(cls, user_id: str, unread_only: bool = False,
                      page: int = 1, per_page: int = 20) -> dict:
        """List notifications for a user, newest first."""
        col = cls._collection()
        if col is None:
            return {"items": [], "total": 0, "page": page, "pages": 0}

        query_filter = {"recipient_id": user_id}
        if unread_only:
            query_filter["is_read"] = False

        total = col.count_documents(query_filter)
        skip = (page - 1) * per_page

        docs = col.find(query_filter).sort("created_at", -1).skip(skip).limit(per_page)
        pages = (total + per_page - 1) // per_page

        return {
            "items": [cls._format(d) for d in docs],
            "total": total,
            "page": page,
            "pages": pages,
        }

    @classmethod
    def mark_read(cls, notification_id: str, user_id: str) -> bool:
        """Mark a single notification as read."""
        col = cls._collection()
        if col is None:
            return False
        result = col.update_one(
            {"_id": notification_id, "recipient_id": user_id},
            {"$set": {"is_read": True}},
        )
        return result.modified_count > 0

    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        """Mark all notifications as read for a user. Returns modified count."""
        col = cls._collection()
        if col is None:
            return 0
        result = col.update_many(
            {"recipient_id": user_id, "is_read": False},
            {"$set": {"is_read": True}},
        )
        return result.modified_count

    @classmethod
    def unread_count(cls, user_id: str) -> int:
        """Get unread notification count for a user."""
        col = cls._collection()
        if col is None:
            return 0
        return col.count_documents({"recipient_id": user_id, "is_read": False})

    @classmethod
    def _format(cls, doc: dict) -> dict:
        return {
            "id": doc.get("_id", doc.get("id", "")),
            "recipient_id": doc.get("recipient_id"),
            "type": doc.get("type"),
            "title": doc.get("title"),
            "body": doc.get("body"),
            "link": doc.get("link"),
            "source_type": doc.get("source_type"),
            "source_id": doc.get("source_id"),
            "is_read": doc.get("is_read", False),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        }
