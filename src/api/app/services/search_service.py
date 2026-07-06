import logging
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from app.extensions import get_mongo_db

logger = logging.getLogger(__name__)


class SearchService:
    """MongoDB full-text search across questions, answers, issues, and projects."""

    COLLECTION = "search_index"
    INDEXED_TYPES = ("question", "answer", "issue", "project")
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
            logger.warning("MongoDB unavailable, search disabled.")
        return cls._mongo_available

    @classmethod
    def _collection(cls):
        if not cls._is_available():
            return None
        return get_mongo_db()[cls.COLLECTION]

    @classmethod
    def index_document(cls, doc_id: str, source_type: str, title: str,
                       body_text: str, tags: list[str] | None = None,
                       created_at: datetime | None = None,
                       extra: dict | None = None):
        try:
            col = cls._collection()
            if col is None:
                return
            if created_at is None:
                created_at = datetime.now(timezone.utc)
            doc = {"doc_id": doc_id, "source_type": source_type, "title": title,
                   "body_text": body_text, "tags": tags or [],
                   "created_at": created_at, "extra": extra or {}}
            col.update_one({"doc_id": doc_id, "source_type": source_type},
                           {"$set": doc}, upsert=True)
        except PyMongoError:
            pass

    @classmethod
    def remove_document(cls, doc_id: str, source_type: str):
        try:
            col = cls._collection()
            if col is None:
                return
            col.delete_one({"doc_id": doc_id, "source_type": source_type})
        except PyMongoError:
            pass

    @classmethod
    def search(cls, q: str, source_type: str | None = None,
               page: int = 1, per_page: int = 20) -> dict:
        empty = {"items": [], "total": 0, "page": page, "pages": 0}
        try:
            col = cls._collection()
            if col is None:
                return empty
            query_filter: dict = {}
            if q:
                query_filter["$text"] = {"$search": q}
            if source_type and source_type in cls.INDEXED_TYPES:
                query_filter["source_type"] = source_type
            total = col.count_documents(query_filter)
            cursor = col.find(query_filter)
            if q:
                cursor = cursor.sort([("score", {"$meta": "textScore"}), ("created_at", -1)])
            else:
                cursor = cursor.sort("created_at", -1)
            skip = (page - 1) * per_page
            cursor = cursor.skip(skip).limit(per_page)
            items = [{"doc_id": d.get("doc_id"), "source_type": d.get("source_type"),
                      "title": d.get("title"), "body_text": d.get("body_text", "")[:200],
                      "tags": d.get("tags", []),
                      "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
                      "extra": d.get("extra", {})} for d in cursor]
            pages = (total + per_page - 1) // per_page
            return {"items": items, "total": total, "page": page, "pages": pages}
        except PyMongoError:
            return empty
