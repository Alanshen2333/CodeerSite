from typing import Optional
from datetime import date
from sqlalchemy import func, case
from app.extensions import db
from app.models.milestone import Milestone
from app.models.issue import Issue


class MilestoneService:
    @staticmethod
    def create_milestone(project_id: str, title: str, description: str = None, due_date: date = None) -> Milestone:
        milestone = Milestone(
            project_id=project_id,
            title=title.strip(),
            description=description,
            due_date=due_date,
        )
        db.session.add(milestone)
        db.session.commit()
        return milestone

    @staticmethod
    def update_milestone(milestone: Milestone, **kwargs) -> Milestone:
        for field in ("title", "description", "due_date", "status"):
            if field in kwargs:
                setattr(milestone, field, kwargs[field])
        db.session.commit()
        return milestone

    @staticmethod
    def delete_milestone(milestone: Milestone):
        # Nullify milestone_id on associated issues
        from app.models.issue import Issue
        Issue.query.filter_by(milestone_id=milestone.id).update({"milestone_id": None})
        db.session.delete(milestone)
        db.session.commit()

    @staticmethod
    def get_milestone(milestone_id: str) -> Optional[Milestone]:
        return db.session.get(Milestone, milestone_id)

    @staticmethod
    def get_milestones(project_id: str) -> list:
        return (
            Milestone.query
            .filter_by(project_id=project_id)
            .order_by(Milestone.created_at.desc())
            .all()
        )

    @staticmethod
    def recompute_counts(milestone_id: str):
        """用 SQL 聚合重算 milestone 的 open/closed issue 计数缓存。"""
        m = db.session.get(Milestone, milestone_id)
        if not m:
            return
        counts = db.session.query(
            func.sum(
                case((Issue.status != "closed", 1), else_=0)
            ).label("open_count"),
            func.sum(
                case((Issue.status == "closed", 1), else_=0)
            ).label("closed_count"),
        ).filter_by(milestone_id=milestone_id).one()
        m.open_issues_count = counts.open_count or 0
        m.closed_issues_count = counts.closed_count or 0
