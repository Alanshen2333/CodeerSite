from typing import Optional
from app.extensions import db
from app.models.comment import Comment
from app.models.question import Question
from app.models.answer import Answer
from app.models.issue import Issue
from app.services.notification_service import NotificationService


class CommentService:
    @staticmethod
    def create_comment(user_id: str, body: str, target_type: str, target_id: str) -> Comment:
        comment = Comment(
            user_id=user_id,
            body=body,
            target_type=target_type,
            target_id=target_id,
        )
        db.session.add(comment)
        db.session.commit()

        # Notify the target owner
        target_author_id = CommentService._get_target_author_id(target_type, target_id)
        if target_author_id and target_author_id != user_id:
            target_label = {"question": "问题", "answer": "回答", "issue": "Issue"}.get(target_type, "内容")
            NotificationService.create(
                recipient_id=target_author_id,
                type_="new_comment",
                title=f"你的{target_label}收到了新评论",
                body=body[:200],
                link=CommentService._build_link(target_type, target_id),
                source_type=target_type,
                source_id=target_id,
            )

        return comment

    @staticmethod
    def _get_target_author_id(target_type: str, target_id: str) -> str | None:
        model_map = {"question": Question, "answer": Answer, "issue": Issue}
        model = model_map.get(target_type)
        if model:
            target = db.session.get(model, target_id)
            return target.author_id if target else None
        return None

    @staticmethod
    def _build_link(target_type: str, target_id: str) -> str:
        if target_type == "question":
            return f"/questions/{target_id}"
        if target_type == "issue":
            return f"/issues/{target_id}"
        # For answers, link to the question
        answer = db.session.get(Answer, target_id)
        if answer:
            return f"/questions/{answer.question_id}#answer-{target_id}"
        return f"/questions/{target_id}"

    @staticmethod
    def update_comment(comment: Comment, body: str) -> Comment:
        comment.body = body
        db.session.commit()
        return comment

    @staticmethod
    def delete_comment(comment: Comment):
        db.session.delete(comment)
        db.session.commit()

    @staticmethod
    def get_comment(comment_id: str) -> Optional[Comment]:
        return db.session.get(Comment, comment_id)

    @staticmethod
    def get_comments(target_type: str, target_id: str, page: int = 1, per_page: int = 20):
        """Get paginated comments for a target."""
        return (
            Comment.query
            .filter_by(target_type=target_type, target_id=target_id)
            .order_by(Comment.created_at.asc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
