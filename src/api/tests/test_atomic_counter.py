"""AtomicCounter 单元测试。

注意：当前测试环境仍为 SQLite，func.greatest 在 SQLite 下不存在；
本测试按 PostgreSQL 语义编写，待 Issue #25 迁移测试环境后启用。
"""

import pytest

from app.extensions import db
from app.models.question import Question
from app.models.user import User
from app.services.atomic_counter import AtomicCounter


@pytest.mark.skip(reason="等待 Issue #25 将测试环境迁移到 PostgreSQL")
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

    def test_no_min_value_allows_negative(self, app, client, auth_headers):
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.reputation = 3
            db.session.commit()

            rows = AtomicCounter.adjust(
                User, user.id, "reputation", -10, min_value=None
            )
            assert rows == 1
            AtomicCounter.refresh(user)
            assert user.reputation == -7
