"""并发竞态测试。

在真实 PostgreSQL 环境下验证锁与唯一约束行为。
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    def test_concurrent_upvotes_keep_count(self, app):
        """多个用户并发对同一问题投 upvote，最终计数准确。"""
        with app.app_context():
            author = User(
                username="qauthor",
                email="qauthor@example.com",
                password_hash="x",
                display_name="Q Author",
            )
            db.session.add(author)
            db.session.commit()
            question = QuestionService.create_question(
                title="并发投票测试", body="body", author_id=author.id
            )

            voters = []
            for i in range(10):
                user = User(
                    username=f"voter{i}",
                    email=f"voter{i}@example.com",
                    password_hash="x",
                    display_name=f"Voter {i}",
                )
                db.session.add(user)
                voters.append(user)
            db.session.commit()
            voter_ids = [u.id for u in voters]
            question_id = question.id
            author_id = author.id

        errors = []

        def vote_worker(user_id):
            try:
                with app.app_context():
                    VoteService.vote(user_id, "up", "question", question_id)
            except Exception as exc:
                errors.append(exc)
            finally:
                with app.app_context():
                    db.session.remove()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(vote_worker, uid) for uid in voter_ids]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors

        with app.app_context():
            q = db.session.get(Question, question_id)
            author_refreshed = db.session.get(User, author_id)
            assert q.vote_count == 10
            assert author_refreshed.reputation == 10 * 10


class TestConcurrentIssueNumber:
    def test_concurrent_create_issue_unique_numbers(self, app):
        """并发创建 Issue，编号唯一且连续。"""
        with app.app_context():
            owner = User(
                username="issueowner",
                email="issueowner@example.com",
                password_hash="x",
                display_name="Issue Owner",
            )
            db.session.add(owner)
            db.session.commit()
            project = ProjectService.create_project(
                owner_id=owner.id, name="并发编号测试"
            )

            creators = []
            for i in range(10):
                user = User(
                    username=f"creator{i}",
                    email=f"creator{i}@example.com",
                    password_hash="x",
                    display_name=f"Creator {i}",
                )
                db.session.add(user)
                creators.append(user)
            db.session.commit()
            creator_ids = [u.id for u in creators]
            project_id = project.id

        errors = []
        created_numbers = []
        lock = threading.Lock()

        def create_worker(user_id):
            try:
                with app.app_context():
                    issue = IssueService.create_issue(
                        project_id=project_id,
                        author_id=user_id,
                        title="并发 Issue",
                    )
                    with lock:
                        created_numbers.append(issue.issue_number)
            except Exception as exc:
                errors.append(exc)
            finally:
                with app.app_context():
                    db.session.remove()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_worker, uid) for uid in creator_ids]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors
        assert len(created_numbers) == 10
        assert sorted(created_numbers) == list(range(1, 11))
        assert len(set(created_numbers)) == 10


class TestConcurrentRegistration:
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
            finally:
                with app.app_context():
                    db.session.remove()

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
    def test_concurrent_star_does_not_lose_count(self, app):
        """多个用户并发 star 同一项目，最终 star_count 准确。"""
        with app.app_context():
            owner = User(
                username="starowner",
                email="starowner@example.com",
                password_hash="x",
                display_name="Star Owner",
            )
            db.session.add(owner)
            db.session.commit()
            project = ProjectService.create_project(
                owner_id=owner.id, name="并发 Star 测试"
            )

            starrers = []
            for i in range(10):
                user = User(
                    username=f"starrer{i}",
                    email=f"starrer{i}@example.com",
                    password_hash="x",
                    display_name=f"Starrer {i}",
                )
                db.session.add(user)
                starrers.append(user)
            db.session.commit()
            starrer_ids = [u.id for u in starrers]
            project_id = project.id

        errors = []

        def star_worker(user_id):
            try:
                with app.app_context():
                    p = db.session.get(Project, project_id)
                    ProjectService.toggle_star(p, user_id)
            except Exception as exc:
                errors.append(exc)
            finally:
                with app.app_context():
                    db.session.remove()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(star_worker, uid) for uid in starrer_ids]
            for f in as_completed(futures):
                f.result()

        assert not errors, errors

        with app.app_context():
            p = db.session.get(Project, project_id)
            assert p.star_count == 10
