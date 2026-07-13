"""徽章自动发放：提问/回答/采纳/投票后自动检查并发放成就徽章。"""

import pytest

from app.extensions import db
from app.models.user import User
from app.models.badge import Badge, UserBadge
from app.services.badge_service import BadgeService


def _login(client, username, email):
    client.post("/api/auth/register", json={
        "username": username, "email": email, "password": "password123",
    })
    resp = client.post("/api/auth/login", json={
        "email": email, "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


def _get_user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


def _get_achievement_badges(app, username):
    """获取用户已获的成就徽章（kind=achievement）列表。"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        return [
            ub for ub in (
                UserBadge.query
                .join(Badge)
                .filter(UserBadge.user_id == user.id, Badge.kind == "achievement")
                .all()
            )
        ]


class TestFirstQuestion:
    def test_first_question_awards_achievement(self, client, app):
        """首次提问后自动发放 first_question 成就。"""
        h = _login(client, "asker", "asker@example.com")
        r = client.post("/api/questions", json={
            "title": "First question", "body": "Hello world",
        }, headers=h)
        assert r.status_code == 201

        badges = _get_achievement_badges(app, "asker")
        slugs = [ub.badge.slug for ub in badges]
        assert "first_question" in slugs

    def test_idempotent_no_duplicate(self, client, app):
        """第二次提问不会重复发放 first_question。"""
        h = _login(client, "asker2", "asker2@example.com")
        client.post("/api/questions", json={
            "title": "Question one", "body": "Body content one",
        }, headers=h)
        client.post("/api/questions", json={
            "title": "Question two", "body": "Body content two",
        }, headers=h)

        badges = _get_achievement_badges(app, "asker2")
        first_q = [ub for ub in badges if ub.badge.slug == "first_question"]
        assert len(first_q) == 1


class TestFirstAnswer:
    def test_first_answer_awards_achievement(self, client, app):
        """首次回答后自动发放 first_answer 成就。"""
        h_asker = _login(client, "qauthor", "qauthor@example.com")
        h_answerer = _login(client, "answerer", "answerer@example.com")

        q = client.post("/api/questions", json={
            "title": "Need help", "body": "Please help",
        }, headers=h_asker).get_json()["question"]

        r = client.post("/api/answers", json={
            "question_id": q["id"], "body": "Here is the answer",
        }, headers=h_answerer)
        assert r.status_code == 201

        badges = _get_achievement_badges(app, "answerer")
        slugs = [ub.badge.slug for ub in badges]
        assert "first_answer" in slugs

    def test_asker_gets_first_question_too(self, client, app):
        """回答者获得 first_answer，提问者已有 first_question。"""
        h_asker = _login(client, "qauthor2", "qauthor2@example.com")
        h_answerer = _login(client, "answerer2", "answerer2@example.com")

        q = client.post("/api/questions", json={
            "title": "Need help 2", "body": "Please help 2",
        }, headers=h_asker).get_json()["question"]

        client.post("/api/answers", json={
            "question_id": q["id"], "body": "Answer here",
        }, headers=h_answerer)

        asker_badges = _get_achievement_badges(app, "qauthor2")
        assert "first_question" in [ub.badge.slug for ub in asker_badges]


class TestAcceptedAchievement:
    def test_accept_awards_answerer(self, client, app):
        """采纳回答后，回答者获得 accepted_1 成就。"""
        h_asker = _login(client, "accepter", "accepter@example.com")
        h_answerer = _login(client, "answered", "answered@example.com")

        q = client.post("/api/questions", json={
            "title": "Accept me", "body": "Question body",
        }, headers=h_asker).get_json()["question"]

        a = client.post("/api/answers", json={
            "question_id": q["id"], "body": "Good answer",
        }, headers=h_answerer).get_json()["answer"]

        r = client.post(f"/api/answers/{a['id']}/accept", headers=h_asker)
        assert r.status_code == 200

        badges = _get_achievement_badges(app, "answered")
        slugs = [ub.badge.slug for ub in badges]
        assert "accepted_1" in slugs
        assert "first_answer" in slugs


class TestReputationAchievement:
    @pytest.mark.skip(reason="SQLite 不支持 greatest()，待测试环境迁移到 PostgreSQL 后启用")
    def test_reputation_threshold_awards(self, client, app):
        """投票使声望跨越 1000 后自动发放 reputation_1000 成就。"""
        h_author = _login(client, "repauthor", "repauthor@example.com")
        h_voter = _login(client, "repvoter", "repvoter@example.com")

        # 作者提问
        q = client.post("/api/questions", json={
            "title": "Rep question", "body": "Body content here",
        }, headers=h_author).get_json()["question"]

        # 直接设置作者声望为 990，一次 upvote (+10) 即到 1000
        author_id = _get_user_id(app, "repauthor")
        with app.app_context():
            user = db.session.get(User, author_id)
            user.reputation = 990
            db.session.commit()

        # 投票者 upvote
        r = client.post("/api/votes", json={
            "target_type": "question", "target_id": q["id"], "vote_type": "up",
        }, headers=h_voter)
        assert r.status_code == 200

        badges = _get_achievement_badges(app, "repauthor")
        slugs = [ub.badge.slug for ub in badges]
        assert "reputation_1000" in slugs

    @pytest.mark.skip(reason="SQLite 不支持 greatest()，待测试环境迁移到 PostgreSQL 后启用")
    def test_downvote_does_not_award_reputation(self, client, app):
        """声望不足 1000 时不发放 reputation_1000。"""
        h_author = _login(client, "lowrep", "lowrep@example.com")
        h_voter = _login(client, "lowvoter", "lowvoter@example.com")

        q = client.post("/api/questions", json={
            "title": "Low rep q", "body": "Body content here",
        }, headers=h_author).get_json()["question"]

        # 声望默认 0，upvote 后 +10 = 10，远不到 1000
        client.post("/api/votes", json={
            "target_type": "question", "target_id": q["id"], "vote_type": "up",
        }, headers=h_voter)

        badges = _get_achievement_badges(app, "lowrep")
        slugs = [ub.badge.slug for ub in badges]
        assert "reputation_1000" not in slugs


class TestMultipleAchievements:
    def test_multiple_unlocks_at_once(self, client, app):
        """一次操作同时解锁多个成就（提问即解锁 first_question）。"""
        h = _login(client, "multi", "multi@example.com")
        client.post("/api/questions", json={
            "title": "Multi Q", "body": "Body content here",
        }, headers=h)

        badges = _get_achievement_badges(app, "multi")
        slugs = [ub.badge.slug for ub in badges]
        assert "first_question" in slugs
        # 还没到 10 题，不应有 questions_10
        assert "questions_10" not in slugs


class TestProfileIntegration:
    def test_profile_shows_achievement_badges(self, client, app):
        """用户 profile API 返回的 awarded_badges 包含成就徽章。"""
        h = _login(client, "profileuser", "profileuser@example.com")
        client.post("/api/questions", json={
            "title": "Profile Q", "body": "Body content here",
        }, headers=h)

        r = client.get("/api/users/profileuser")
        assert r.status_code == 200
        data = r.get_json()

        # achievements 是计算值
        ach_keys = [a["key"] for a in data["achievements"]]
        assert "first_question" in ach_keys

        # awarded_badges 包含持久化的成就徽章
        awarded = data["awarded_badges"]
        achievement_awards = [
            ub for ub in awarded if ub["badge"]["kind"] == "achievement"
        ]
        assert len(achievement_awards) >= 1
        assert achievement_awards[0]["badge"]["slug"] == "first_question"
