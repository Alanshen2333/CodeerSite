from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.jwt_blocklist import JWTBlocklist


class JWTBlocklistService:
    """JWT 吊销写/查闭环（PostgreSQL）。"""

    @staticmethod
    def revoke(
        jti: str,
        user_id: str,
        token_type: str,
        expires_at: datetime | None = None,
    ) -> bool:
        try:
            existing = db.session.get(JWTBlocklist, jti)
            if existing is None:
                db.session.add(
                    JWTBlocklist(
                        jti=jti,
                        user_id=user_id,
                        token_type=token_type,
                        expires_at=expires_at,
                    )
                )
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @staticmethod
    def is_revoked(jti: str) -> bool:
        return db.session.get(JWTBlocklist, jti) is not None
