import re
from app.extensions import db
from app.models.user import User
from app.models.question import Question
from app.models.answer import Answer
from app.models.badge import Badge, UserBadge

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

    # 成就条件仅允许「变量 操作符 整数」的简单比较，拒绝 eval 以防代码注入。
    _CONDITION_RE = re.compile(
        r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(>=|<=|==|>|<)\s*(\d+)\s*$"
    )

    @staticmethod
    def _check_condition(condition: str, questions: int, answers: int,
                          accepted: int, reputation: int) -> bool:
        if not isinstance(condition, str):
            return False

        match = BadgeService._CONDITION_RE.match(condition)
        if not match:
            return False

        key, op, raw_value = match.groups()
        allowed_keys = {"questions", "answers", "accepted", "reputation"}
        if key not in allowed_keys:
            return False

        try:
            value = int(raw_value)
        except ValueError:
            return False

        namespace = {
            "questions": questions,
            "answers": answers,
            "accepted": accepted,
            "reputation": reputation,
        }
        actual = namespace[key]

        if op == ">=":
            return actual >= value
        if op == "<=":
            return actual <= value
        if op == ">":
            return actual > value
        if op == "<":
            return actual < value
        if op == "==":
            return actual == value
        return False

    # ── 自定义徽章定义 CRUD ─────────────────────────────

    @staticmethod
    def list_badges():
        """列出所有自定义徽章定义（按创建时间倒序）。"""
        return Badge.query.order_by(Badge.created_at.desc()).all()

    @staticmethod
    def get_badge(badge_id: str) -> Badge | None:
        return db.session.get(Badge, badge_id)

    @staticmethod
    def get_badge_by_slug(slug: str) -> Badge | None:
        return Badge.query.filter_by(slug=slug).first()

    @staticmethod
    def create_badge(name: str, description: str | None = None,
                     icon: str | None = None, color: str = "#5e6ad2") -> Badge:
        """创建自定义徽章。name 唯一，自动生成 slug。"""
        name = name.strip()
        if Badge.query.filter_by(name=name).first():
            raise ValueError("Badge name already exists.")
        slug = BadgeService._slugify(name)
        base = slug
        i = 1
        while Badge.query.filter_by(slug=slug).first():
            slug = f"{base}-{i}"
            i += 1
        badge = Badge(
            name=name,
            slug=slug,
            description=description,
            icon=icon,
            color=color,
            kind="custom",
        )
        db.session.add(badge)
        db.session.flush()
        return badge

    @staticmethod
    def update_badge(badge: Badge, data: dict) -> Badge:
        """更新徽章字段。name 改动时同步 slug（保持唯一）。"""
        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            if not new_name:
                raise ValueError("Badge name cannot be empty.")
            existing = Badge.query.filter_by(name=new_name).first()
            if existing and existing.id != badge.id:
                raise ValueError("Badge name already exists.")
            badge.name = new_name
            # 重生成 slug 仅当当前 slug 与旧 name 不一致或冲突时
            new_slug = BadgeService._slugify(new_name)
            if new_slug != badge.slug:
                base = new_slug
                i = 1
                while Badge.query.filter_by(slug=new_slug).first() is not None and \
                        Badge.query.filter_by(slug=new_slug).first().id != badge.id:
                    new_slug = f"{base}-{i}"
                    i += 1
                badge.slug = new_slug
        if "description" in data:
            badge.description = data["description"]
        if "icon" in data:
            badge.icon = data["icon"]
        if "color" in data and data["color"]:
            badge.color = data["color"]
        db.session.flush()
        return badge

    @staticmethod
    def delete_badge(badge: Badge) -> None:
        """删除徽章定义（级联删除发放关系）。"""
        db.session.delete(badge)
        db.session.flush()

    # ── 发放 / 撤销 ─────────────────────────────────────

    @staticmethod
    def award(badge: Badge, user_id: str, awarded_by: str | None,
              reason: str | None = None) -> UserBadge:
        """向用户发放徽章；已发放则抛 ValueError。"""
        if not db.session.get(User, user_id):
            raise LookupError("User not found.")
        existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
        if existing:
            raise ValueError("User already has this badge.")
        ub = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            awarded_by=awarded_by,
            reason=reason,
        )
        db.session.add(ub)
        db.session.flush()
        return ub

    @staticmethod
    def revoke(badge: Badge, user_id: str) -> None:
        """撤销用户徽章；不存在则抛 LookupError。"""
        ub = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
        if not ub:
            raise LookupError("User does not have this badge.")
        db.session.delete(ub)
        db.session.flush()

    @staticmethod
    def get_recipients(badge: Badge) -> list[UserBadge]:
        return (
            UserBadge.query
            .filter_by(badge_id=badge.id)
            .order_by(UserBadge.created_at.desc())
            .all()
        )

    @staticmethod
    def get_user_awarded_badges(user_id: str) -> list[UserBadge]:
        """用户已获的自定义徽章列表。"""
        return (
            UserBadge.query
            .filter_by(user_id=user_id)
            .order_by(UserBadge.created_at.desc())
            .all()
        )

    @staticmethod
    def _slugify(name: str) -> str:
        """名称转 URL-safe slug（与 tag_service 一致策略）。"""
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-") or "badge"
