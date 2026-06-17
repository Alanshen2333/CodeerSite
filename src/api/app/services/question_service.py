from typing import List, Optional, Tuple
import mistune
from app.extensions import db
from app.models.question import Question
from app.models.tag import Tag
from app.services.tag_service import TagService
from app.services.search_service import SearchService


_md_renderer = mistune.create_markdown(escape=True, hard_wrap=True)


class QuestionService:
    @staticmethod
    def create_question(
        author_id: str, title: str, body: str, tag_ids: Optional[List[str]] = None
    ) -> Question:
        """Create a new question with optional tags."""
        body_html = _md_renderer(body)

        question = Question(
            title=title.strip(),
            body=body,
            body_html=body_html,
            author_id=author_id,
        )
        db.session.add(question)
        db.session.flush()  # Get question.id

        # Associate tags
        if tag_ids:
            tags = db.session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            question.tags = tags
            # Update usage counts
            TagService.update_usage_counts(tag_ids)

        db.session.commit()
        QuestionService._index_to_search(question)
        return question

    @staticmethod
    def update_question(
        question: Question, title: str = None, body: str = None, tag_ids: List[str] = None
    ) -> Question:
        """Update question fields."""
        if title is not None:
            question.title = title.strip()
        if body is not None:
            question.body = body
            question.body_html = _md_renderer(body)
        if tag_ids is not None:
            old_tag_ids = [t.id for t in question.tags]
            tags = db.session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            question.tags = tags
            # Recalculate usage counts for affected tags
            affected = set(old_tag_ids) | set(tag_ids)
            TagService.update_usage_counts(list(affected))

        db.session.commit()
        QuestionService._index_to_search(question)
        return question

    @staticmethod
    def get_question(question_id: str) -> Optional[Question]:
        return db.session.get(Question, question_id)

    @staticmethod
    def delete_question(question: Question):
        """Delete question and associated tags' usage counts."""
        tag_ids = [t.id for t in question.tags]
        QuestionService._remove_from_search(question)
        db.session.delete(question)
        db.session.flush()
        TagService.update_usage_counts(tag_ids)
        db.session.commit()

    @staticmethod
    def get_questions(
        page: int = 1,
        per_page: int = 20,
        sort: str = "newest",
        tag_slug: str = None,
        filter_type: str = None,
    ) -> Tuple:
        """Get paginated questions with sorting and filtering.

        sort: newest | popular | unanswered
        filter_type: all | closed | pinned
        """
        query = Question.query

        # Filter by tag
        if tag_slug:
            tag = Tag.query.filter_by(slug=tag_slug).first()
            if tag:
                query = query.filter(Question.tags.contains(tag))

        # Filter by type
        if filter_type == "closed":
            query = query.filter_by(is_closed=True)
        elif filter_type == "pinned":
            query = query.filter_by(is_pinned=True)

        # Sort
        if sort == "popular":
            query = query.order_by(Question.vote_count.desc())
        elif sort == "unanswered":
            query = query.filter_by(answer_count=0).order_by(Question.created_at.desc())
        else:  # newest
            query = query.order_by(Question.created_at.desc())

        # Pinned always on top
        query = query.order_by(Question.is_pinned.desc(), Question.created_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def close_question(question: Question) -> Question:
        question.is_closed = True
        db.session.commit()
        return question

    @staticmethod
    def reopen_question(question: Question) -> Question:
        question.is_closed = False
        db.session.commit()
        return question

    @staticmethod
    def toggle_pin(question: Question) -> Question:
        question.is_pinned = not question.is_pinned
        db.session.commit()
        return question

    @staticmethod
    def increment_view(question: Question):
        """Increment view count atomically."""
        question.view_count = Question.view_count + 1
        db.session.commit()

    @staticmethod
    def _index_to_search(question: Question):
        tag_names = [t.name for t in question.tags] if question.tags else []
        SearchService.index_document(
            doc_id=question.id,
            source_type="question",
            title=question.title,
            body_text=question.body[:1000],
            tags=tag_names,
            created_at=question.created_at,
            extra={"author_name": question.author.display_name if question.author else None},
        )

    @staticmethod
    def _remove_from_search(question: Question):
        SearchService.remove_document(question.id, "question")
