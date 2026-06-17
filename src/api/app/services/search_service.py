from datetime import datetime, timezone
from app.extensions import get_mongo_db


class SearchService:
    """MongoDB full-text search across questions, answers, issues, and projects."""

    COLLECTION = "search_index"

    INDEXED_TYPES = ("question", "answer", "issue", "project")

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
            [("title", "text"), ("body_text", "text")],
            name="search_text_idx",
        )
        col.create_index(
            [("source_type", 1), ("created_at", -1)],
            name="search_type_date_idx",
        )
        col.create_index("tags", name="search_tags_idx")

    @classmethod
    def index_document(cls, doc_id: str, source_type: str, title: str,
                       body_text: str, tags: list[str] | None = None,
                       created_at: datetime | None = None,
                       extra: dict | None = None):
        """Upsert a single document into the search index."""
        col = cls._collection()
        if col is None:
            return
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        doc = {
            "doc_id": doc_id,
            "source_type": source_type,
            "title": title,
            "body_text": body_text,
            "tags": tags or [],
            "created_at": created_at,
            "extra": extra or {},
        }
        col.update_one(
            {"doc_id": doc_id, "source_type": source_type},
            {"$set": doc},
            upsert=True,
        )

    @classmethod
    def remove_document(cls, doc_id: str, source_type: str):
        """Remove a document from the search index."""
        col = cls._collection()
        if col is None:
            return
        col.delete_one({"doc_id": doc_id, "source_type": source_type})

    @classmethod
    def search(cls, q: str, source_type: str | None = None,
               page: int = 1, per_page: int = 20) -> dict:
        """Full-text search. Returns paginated results with relevance scores."""
        col = cls._collection()
        if col is None:
            return {"items": [], "total": 0, "page": page, "pages": 0}

        query_filter: dict = {}
        if q:
            query_filter["$text"] = {"$search": q}
        if source_type and source_type in cls.INDEXED_TYPES:
            query_filter["source_type"] = source_type

        total = col.count_documents(query_filter)

        cursor = col.find(query_filter)
        if q:
            cursor = cursor.sort([("score", {"$meta": "textScore"})])
        cursor = cursor.sort("created_at", -1)

        skip = (page - 1) * per_page
        cursor = cursor.skip(skip).limit(per_page)

        items = []
        for doc in cursor:
            items.append({
                "doc_id": doc.get("doc_id"),
                "source_type": doc.get("source_type"),
                "title": doc.get("title"),
                "body_text": doc.get("body_text", "")[:200],
                "tags": doc.get("tags", []),
                "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
                "extra": doc.get("extra", {}),
            })

        pages = (total + per_page - 1) // per_page
        return {"items": items, "total": total, "page": page, "pages": pages}
