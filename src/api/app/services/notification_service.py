import uuid
import logging
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from app.extensions import get_mongo_db

logger = logging.getLogger(__name__)


class NotificationService:
    """MongoDB-backed notification system with TTL auto-cleanup."""

    COLLECTION = "notifications"
    TTL_SECONDS = 90 * 24 * 3600
    _mongo_available: bool | None = None

    @classmethod
    def _is_available(cls) -> bool:
        if cls._mongo_available is not None:
            return cls._mongo_available
        db = get_mongo_db()
        if db is None:
            cls._mongo_available = False
            return False
        try:
            db.command("ping")
            cls._mongo_available = True
        except PyMongoError:
            cls._mongo_available = False
            logger.warning("MongoDB unavailable, notifications disabled.")
        return cls._mongo_available

    @classmethod
    def _collection(cls):
        if not cls._is_available():
            return None
        return get_mongo_db()[cls.COLLECTION]

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
        except PyMongoError:
            return {}

    @classmethod
    def list_for_user(
        cls, user_id: str, unread_only: bool = False, page: int = 1, per_page: int = 20
    ) -> dict:
        empty = {"items": [], "total": 0, "page": page, "pages": 0}
        try:
            col = cls._collection()
            if col is None:
                return empty
            query_filter = {"recipient_id": user_id}
            if unread_only:
                query_filter["is_read"] = False
            total = col.count_documents(query_filter)
            skip = (page - 1) * per_page
            docs = (
                col.find(query_filter).sort("created_at", -1).skip(skip).limit(per_page)
            )
            pages = (total + per_page - 1) // per_page
            return {
                "items": [cls._format(d) for d in docs],
                "total": total,
                "page": page,
                "pages": pages,
            }
        except PyMongoError:
            return empty

    @classmethod
    def mark_read(cls, notification_id: str, user_id: str) -> bool:
        try:
            col = cls._collection()
            if col is None:
                return False
            result = col.update_one(
                {"_id": notification_id, "recipient_id": user_id},
                {"$set": {"is_read": True}},
            )
            return result.modified_count > 0
        except PyMongoError:
            return False

    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        try:
            col = cls._collection()
            if col is None:
                return 0
            result = col.update_many(
                {"recipient_id": user_id, "is_read": False},
                {"$set": {"is_read": True}},
            )
            return result.modified_count
        except PyMongoError:
            return 0

    @classmethod
    def unread_count(cls, user_id: str) -> int:
        try:
            col = cls._collection()
            if col is None:
                return 0
            return col.count_documents({"recipient_id": user_id, "is_read": False})
        except PyMongoError:
            return 0

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
            "created_at": doc["created_at"].isoformat()
            if doc.get("created_at")
            else None,
        }
