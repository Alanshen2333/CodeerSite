from typing import Optional
import mistune
from app.extensions import db
from app.models.answer import Answer
from app.models.question import Question
from app.services.atomic_counter import AtomicCounter
from app.services.search_service import SearchService
from app.services.notification_service import NotificationService


_md_renderer = mistune.create_markdown(escape=True, hard_wrap=True)


class AnswerService:
    @staticmethod
    def create_answer(question_id: str, author_id: str, body: str) -> Answer:
        """Create an answer and increment question answer_count."""
        question = db.session.get(Question, question_id)
        if not question:
            raise ValueError("Question not found.")

        body_html = _md_renderer(body)

        answer = Answer(
            question_id=question_id,
            author_id=author_id,
            body=body,
            body_html=body_html,
        )
        db.session.add(answer)

        # Update question answer_count
        question.answer_count = Question.answer_count + 1

        db.session.commit()
        AnswerService._index_to_search(answer, question)

        # Notify question author
        if question.author_id != author_id:
            NotificationService.create(
                recipient_id=question.author_id,
                type_="new_answer",
                title=f"{answer.author.display_name or '有人'} 回答了你的问题",
                body=answer.body[:200],
                link=f"/questions/{question.id}#answer-{answer.id}",
                source_type="answer",
                source_id=answer.id,
            )

        return answer

    @staticmethod
    def update_answer(answer: Answer, body: str) -> Answer:
        answer.body = body
        answer.body_html = _md_renderer(body)
        db.session.commit()
        AnswerService._index_to_search(answer, answer.question)
        return answer

    @staticmethod
    def delete_answer(answer: Answer):
        """Delete answer and decrement question answer_count."""
        question = db.session.get(Question, answer.question_id)
        AnswerService._remove_from_search(answer)
        db.session.delete(answer)
        db.session.flush()
        if question:
            # If this was the accepted answer, clear it
            if question.accepted_answer_id == answer.id:
                question.accepted_answer_id = None
            AtomicCounter.adjust(Question, question.id, "answer_count", -1)
        db.session.commit()

    @staticmethod
    def accept_answer(answer: Answer, question_author_id: str) -> Answer:
        """Accept an answer. Only the question author can do this."""
        question = db.session.get(Question, answer.question_id)
        if not question:
            raise ValueError("Question not found.")
        if question.author_id != question_author_id:
            raise PermissionError("Only the question author can accept an answer.")

        # Un-accept previous accepted answer
        if question.accepted_answer_id:
            prev = db.session.get(Answer, question.accepted_answer_id)
            if prev:
                prev.is_accepted = False

        # Accept this answer
        answer.is_accepted = True
        question.accepted_answer_id = answer.id
        db.session.commit()

        # Notify answer author
        if answer.author_id != question_author_id:
            NotificationService.create(
                recipient_id=answer.author_id,
                type_="answer_accepted",
                title="你的回答被采纳了",
                body=answer.body[:200],
                link=f"/questions/{question.id}#answer-{answer.id}",
                source_type="answer",
                source_id=answer.id,
            )

        return answer

    @staticmethod
    def unaccept_answer(answer: Answer, question_author_id: str):
        """Un-accept an answer."""
        question = db.session.get(Question, answer.question_id)
        if not question:
            raise ValueError("Question not found.")
        if question.author_id != question_author_id:
            raise PermissionError("Only the question author can un-accept an answer.")

        answer.is_accepted = False
        question.accepted_answer_id = None
        db.session.commit()

    @staticmethod
    def get_answer(answer_id: str) -> Optional[Answer]:
        return db.session.get(Answer, answer_id)

    @staticmethod
    def get_answers(question_id: str, page: int = 1, per_page: int = 20):
        """Get paginated answers for a question, accepted first then by votes."""
        return (
            Answer.query
            .filter_by(question_id=question_id)
            .order_by(Answer.is_accepted.desc(), Answer.vote_count.desc(), Answer.created_at.asc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def _index_to_search(answer: Answer, question: Question | None = None):
        q_title = question.title if question else ""
        SearchService.index_document(
            doc_id=answer.id,
            source_type="answer",
            title=f"Re: {q_title}" if q_title else answer.body[:80],
            body_text=answer.body[:1000],
            created_at=answer.created_at,
            extra={"question_id": answer.question_id, "author_name": answer.author.display_name if answer.author else None},
        )

    @staticmethod
    def _remove_from_search(answer: Answer):
        SearchService.remove_document(answer.id, "answer")
