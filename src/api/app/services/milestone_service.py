from typing import Optional
from datetime import date
from app.extensions import db
from app.models.milestone import Milestone


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
