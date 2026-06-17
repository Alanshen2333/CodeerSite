from typing import Optional
from app.extensions import db
from app.models.bookmark import Bookmark


class BookmarkService:
    @staticmethod
    def toggle_bookmark(user_id: str, target_type: str, target_id: str) -> tuple:
        """Toggle a bookmark. Returns (bookmark, created) where created is bool."""
        existing = Bookmark.query.filter_by(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return (None, False)

        bookmark = Bookmark(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
        )
        db.session.add(bookmark)
        db.session.commit()
        return (bookmark, True)

    @staticmethod
    def is_bookmarked(user_id: str, target_type: str, target_id: str) -> bool:
        return Bookmark.query.filter_by(
            user_id=user_id, target_type=target_type, target_id=target_id
        ).first() is not None

    @staticmethod
    def get_user_bookmarks(user_id: str, target_type: str = None, page: int = 1, per_page: int = 20):
        """Get paginated bookmarks for a user, optionally filtered by target_type."""
        query = Bookmark.query.filter_by(user_id=user_id)
        if target_type:
            query = query.filter_by(target_type=target_type)
        return query.order_by(Bookmark.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
