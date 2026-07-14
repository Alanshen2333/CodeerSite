"""AtomicCounter 单元测试。

测试环境为 PostgreSQL，func.greatest 在此可用。
"""

from app.extensions import db
from app.models.question import Question
from app.models.user import User
from app.services.atomic_counter import AtomicCounter


class TestAtomicCounter:
    def test_positive_delta_updates(self, app, client, auth_headers):
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            question = Question(
                title="计数测试",
                body="body",
                body_html="<p>body</p>",
                author_id=user.id,
                vote_count=5,
            )
            db.session.add(question)
            db.session.commit()

            rows = AtomicCounter.adjust(Question, question.id, "vote_count", 3)
            assert rows == 1
            AtomicCounter.refresh(question)
            assert question.vote_count == 8

    def test_negative_delta_clamps_to_zero(self, app, client, auth_headers):
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            question = Question(
                title="下限测试",
                body="body",
                body_html="<p>body</p>",
                author_id=user.id,
                vote_count=1,
            )
            db.session.add(question)
            db.session.commit()

            rows = AtomicCounter.adjust(Question, question.id, "vote_count", -5)
            assert rows == 1
            AtomicCounter.refresh(question)
            assert question.vote_count == 0

    def test_reputation_can_clamp_to_zero(self, app, client, auth_headers):
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.reputation = 2
            db.session.commit()

            rows = AtomicCounter.adjust(User, user.id, "reputation", -10)
            assert rows == 1
            AtomicCounter.refresh(user)
            assert user.reputation == 0

    def test_zero_delta_does_nothing(self, app, client, auth_headers):
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            question = Question(
                title="零 delta 测试",
                body="body",
                body_html="<p>body</p>",
                author_id=user.id,
                vote_count=7,
            )
            db.session.add(question)
            db.session.commit()

            rows = AtomicCounter.adjust(Question, question.id, "vote_count", 0)
            assert rows == 0
            AtomicCounter.refresh(question)
            assert question.vote_count == 7

    def test_no_min_value_uses_plain_expression(self, app, client, auth_headers):
        """min_value=None 时不使用 GREATEST clamp，直接做加减。"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.reputation = 5
            db.session.commit()

            rows = AtomicCounter.adjust(User, user.id, "reputation", -3, min_value=None)
            assert rows == 1
            AtomicCounter.refresh(user)
            assert user.reputation == 2
