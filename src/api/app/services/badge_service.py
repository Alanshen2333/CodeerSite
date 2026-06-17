from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer

BADGE_TIERS = [
    {"key": "newcomer", "name": "新人", "color": "#8c8c8c", "min_reputation": 0},
    {"key": "bronze", "name": "青铜", "color": "#cd7f32", "min_reputation": 100},
    {"key": "silver", "name": "白银", "color": "#a8a8a8", "min_reputation": 500},
    {"key": "gold", "name": "黄金", "color": "#ffc107", "min_reputation": 2000},
    {"key": "platinum", "name": "铂金", "color": "#1890ff", "min_reputation": 5000},
    {"key": "diamond", "name": "钻石", "color": "#722ed1", "min_reputation": 10000},
]

ACHIEVEMENTS = [
    {"key": "first_question", "name": "初次提问", "icon": "❓", "condition": "questions >= 1"},
    {"key": "first_answer", "name": "初次回答", "icon": "💬", "condition": "answers >= 1"},
    {"key": "accepted_1", "name": "被采纳", "icon": "✅", "condition": "accepted >= 1"},
    {"key": "accepted_10", "name": "优质贡献者", "icon": "🌟", "condition": "accepted >= 10"},
    {"key": "accepted_50", "name": "社区专家", "icon": "🏆", "condition": "accepted >= 50"},
    {"key": "questions_10", "name": "勤学好问", "icon": "📚", "condition": "questions >= 10"},
    {"key": "questions_50", "name": "问题达人", "icon": "🎯", "condition": "questions >= 50"},
    {"key": "answers_10", "name": "乐于助人", "icon": "🤝", "condition": "answers >= 10"},
    {"key": "answers_50", "name": "社区导师", "icon": "👨‍🏫", "condition": "answers >= 50"},
    {"key": "reputation_1000", "name": "声望过千", "icon": "💎", "condition": "reputation >= 1000"},
]


class BadgeService:
    @staticmethod
    def get_user_badge(user: User) -> dict:
        """Get the reputation tier badge for a user."""
        tier = BADGE_TIERS[0]
        for t in BADGE_TIERS:
            if user.reputation >= t["min_reputation"]:
                tier = t
        return tier

    @staticmethod
    def get_user_achievements(user: User) -> list[dict]:
        """Get unlocked achievements for a user based on their stats."""
        question_count = Question.query.filter_by(author_id=user.id).count()
        answer_count = Answer.query.filter_by(author_id=user.id).count()
        accepted_count = Answer.query.filter_by(author_id=user.id, is_accepted=True).count()

        unlocked = []
        for ach in ACHIEVEMENTS:
            cond = ach["condition"]
            if BadgeService._check_condition(cond, question_count, answer_count,
                                              accepted_count, user.reputation):
                unlocked.append(ach)
        return unlocked

    @staticmethod
    def get_next_tier(user: User) -> dict | None:
        """Get the next reputation tier the user can reach."""
        for t in BADGE_TIERS:
            if user.reputation < t["min_reputation"]:
                return {
                    "key": t["key"],
                    "name": t["name"],
                    "color": t["color"],
                    "remaining": t["min_reputation"] - user.reputation,
                }
        return None

    @staticmethod
    def _check_condition(condition: str, questions: int, answers: int,
                          accepted: int, reputation: int) -> bool:
        namespace = {
            "questions": questions,
            "answers": answers,
            "accepted": accepted,
            "reputation": reputation,
        }
        try:
            return bool(eval(condition, {"__builtins__": {}}, namespace))
        except Exception:
            return False
