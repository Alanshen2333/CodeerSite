from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer


class UserService:
    @staticmethod
    def get_users(page: int = 1, per_page: int = 20):
        """Get paginated users sorted by reputation."""
        return (
            User.query
            .filter_by(is_active=True)
            .order_by(User.reputation.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
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
