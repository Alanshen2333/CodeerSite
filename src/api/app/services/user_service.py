import io
from datetime import datetime, timezone
from PIL import Image
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer


class UserService:
    @staticmethod
    def get_users(page: int = 1, per_page: int = 20, q: str = None):
        """Get paginated users sorted by reputation. q 模糊匹配 username/display_name。"""
        query = User.query.filter_by(is_active=True)
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(User.username.ilike(like), User.display_name.ilike(like))
            )
        return query.order_by(User.reputation.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_user_by_username(username: str) -> User | None:
        """Get user by username (active users only)."""
        return User.query.filter_by(username=username, is_active=True).first()

    @staticmethod
    def get_user_stats(user_id: str) -> dict:
        """Get user contribution stats."""
        return {
            "question_count": Question.query.filter_by(author_id=user_id).count(),
            "answer_count": Answer.query.filter_by(author_id=user_id).count(),
            "accepted_count": Answer.query.filter_by(author_id=user_id, is_accepted=True).count(),
            "project_count": 0,  # Not yet implemented
        }

    @staticmethod
    def update_profile(user: User, data: dict) -> User:
        """更新用户个人资料字段。"""
        allowed = {"display_name", "bio", "website", "location", "avatar_url"}
        for field, value in data.items():
            if field in allowed and value is not None:
                setattr(user, field, value)
        db.session.commit()
        return user

    @staticmethod
    def save_avatar(user: User, file_stream, mime_type: str) -> User:
        """校验、缩放并保存头像 blob。

        - 仅接受 image/png / image/jpeg / image/webp
        - 最大边不超过 512，超过则等比缩放
        - 文件原始大小不超过 MAX_AVATAR_SIZE（默认 2MB）
        - 保存为 PNG 以统一格式
        """
        allowed_types = {"image/png", "image/jpeg", "image/webp"}
        if mime_type not in allowed_types:
            raise ValueError("仅支持 PNG、JPEG、WebP 格式的图片。")

        max_size = current_app.config.get("MAX_AVATAR_SIZE", 2 * 1024 * 1024)
        raw = file_stream.read()
        if len(raw) > max_size:
            raise ValueError(f"图片大小不能超过 {max_size // 1024 // 1024}MB。")

        try:
            img = Image.open(io.BytesIO(raw))
        except Exception as exc:
            raise ValueError("无法解析图片文件。") from exc

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        max_edge = 512
        if max(img.width, img.height) > max_edge:
            img.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)

        out = io.BytesIO()
        img.save(out, format="PNG", optimize=True)
        out.seek(0)

        user.avatar_blob = out.read()
        user.avatar_mime_type = "image/png"
        user.avatar_updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return user
