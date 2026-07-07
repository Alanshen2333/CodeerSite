"""并发竞态测试。

注意：当前测试环境仍为 SQLite，这些测试按 PostgreSQL 语义编写；
在 SQLite 下跳过，待 Issue #25 迁移测试环境后启用。
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from app.extensions import db
from app.models.project import Project
from app.models.question import Question
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.issue_service import IssueService
from app.services.project_service import ProjectService
from app.services.question_service import QuestionService
from app.services.vote_service import VoteService


class TestConcurrentVotes:
    @pytest.mark.skip(reason="等待 Issue #25 将测试环境迁移到 PostgreSQL")
    def test_concurrent_upvotes_keep_count(self, app):
        """多个用户并发对同一问题投 upvote，最终计数准确。"""
        with app.app_context():
            author = User(
                username="qauthor", email="qauthor@example.com",
                password_hash="x", display_name="Q Author",
            )
            db.session.add(author)
            db.session.commit()
            question = QuestionService.create_question(
                title="并发投票测试", body="body", author_id=author.id
            )

            voters = []
            for i in range(10):
                user = User(
                    username=f"voter{i}", email=f"voter{i}@example.com",
                    password_hash="x", display_name=f"Voter {i}",
                )
                db.session.add(user)
                voters.append(user)
            db.session.commit()

        errors = []

        def vote_worker(user_id):
            try:
                with app.app_context():
                    VoteService.vote(user_id, "up", "question", question.id)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(vote_worker, u.id) for u in voters]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors

        with app.app_context():
            q = db.session.get(Question, question.id)
            author_refreshed = db.session.get(User, author.id)
            assert q.vote_count == 10
            assert author_refreshed.reputation == 10 * 10


class TestConcurrentIssueNumber:
    @pytest.mark.skip(reason="等待 Issue #25 将测试环境迁移到 PostgreSQL")
    def test_concurrent_create_issue_unique_numbers(self, app):
        """并发创建 Issue，编号唯一且连续。"""
        with app.app_context():
            owner = User(
                username="issueowner", email="issueowner@example.com",
                password_hash="x", display_name="Issue Owner",
            )
            db.session.add(owner)
            db.session.commit()
            project = ProjectService.create_project(
                owner_id=owner.id, name="并发编号测试"
            )

            creators = []
            for i in range(10):
                user = User(
                    username=f"creator{i}", email=f"creator{i}@example.com",
                    password_hash="x", display_name=f"Creator {i}",
                )
                db.session.add(user)
                creators.append(user)
            db.session.commit()

        errors = []
        created_numbers = []
        lock = threading.Lock()

        def create_worker(user_id):
            try:
                with app.app_context():
                    issue = IssueService.create_issue(
                        project_id=project.id,
                        author_id=user_id,
                        title="并发 Issue",
                    )
                    with lock:
                        created_numbers.append(issue.issue_number)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_worker, u.id) for u in creators]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors
        assert len(created_numbers) == 10
        assert sorted(created_numbers) == list(range(1, 11))
        assert len(set(created_numbers)) == 10


class TestConcurrentRegistration:
    @pytest.mark.skip(reason="等待 Issue #25 将测试环境迁移到 PostgreSQL")
    def test_concurrent_same_username_creates_one_user(self, app):
        """并发注册相同用户名/邮箱，最终只应存在一条用户记录。"""
        errors = []
        success_count = 0
        lock = threading.Lock()

        def register_worker(_):
            try:
                with app.app_context():
                    AuthService.register_user(
                        username="dupuser",
                        email="dup@example.com",
                        password="password123",
                    )
                    with lock:
                        nonlocal success_count
                        success_count += 1
            except ValueError as exc:
                # 预期大部分线程会得到重复错误
                if "already" not in str(exc).lower():
                    errors.append(exc)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_worker, i) for i in range(10)]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors
        assert success_count == 1

        with app.app_context():
            users = User.query.filter_by(username="dupuser").all()
            assert len(users) == 1
            assert users[0].email == "dup@example.com"


class TestConcurrentStar:
    @pytest.mark.skip(reason="等待 Issue #25 将测试环境迁移到 PostgreSQL")
    def test_concurrent_star_does_not_lose_count(self, app):
        """多个用户并发 star 同一项目，最终 star_count 准确。"""
        with app.app_context():
            owner = User(
                username="starowner", email="starowner@example.com",
                password_hash="x", display_name="Star Owner",
            )
            db.session.add(owner)
            db.session.commit()
            project = ProjectService.create_project(
                owner_id=owner.id, name="并发 Star 测试"
            )

            starrers = []
            for i in range(10):
                user = User(
                    username=f"starrer{i}", email=f"starrer{i}@example.com",
                    password_hash="x", display_name=f"Starrer {i}",
                )
                db.session.add(user)
                starrers.append(user)
            db.session.commit()

        errors = []

        def star_worker(user_id):
            try:
                with app.app_context():
                    ProjectService.toggle_star(project, user_id)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(star_worker, u.id) for u in starrers]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors

        with app.app_context():
            p = db.session.get(Project, project.id)
            assert p.star_count == 10
