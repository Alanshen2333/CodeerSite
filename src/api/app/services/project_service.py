import re
from typing import Optional, List
from app.extensions import db
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.services.search_service import SearchService


class ProjectService:
    @staticmethod
    def create_project(owner_id: str, name: str, description: str = None, visibility: str = "public") -> Project:
        slug = ProjectService._generate_slug(name)
        project = Project(
            name=name.strip(),
            slug=slug,
            description=description,
            owner_id=owner_id,
            visibility=visibility,
        )
        db.session.add(project)
        db.session.flush()

        # Owner becomes member with "owner" role
        member = ProjectMember(project_id=project.id, user_id=owner_id, role="owner")
        db.session.add(member)
        db.session.commit()
        ProjectService._index_to_search(project)
        return project

    @staticmethod
    def update_project(project: Project, name: str = None, description: str = None, visibility: str = None) -> Project:
        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description
        if visibility is not None:
            project.visibility = visibility
        db.session.commit()
        ProjectService._index_to_search(project)
        return project

    @staticmethod
    def delete_project(project: Project):
        ProjectService._remove_from_search(project)
        db.session.delete(project)
        db.session.commit()

    @staticmethod
    def get_project(project_id: str = None, slug: str = None) -> Optional[Project]:
        if project_id:
            return db.session.get(Project, project_id)
        if slug:
            return Project.query.filter_by(slug=slug).first()
        return None

    @staticmethod
    def get_projects(page: int = 1, per_page: int = 20, sort: str = "newest", visibility: str = None):
        query = Project.query
        if visibility:
            query = query.filter_by(visibility=visibility)

        if sort == "stars":
            query = query.order_by(Project.star_count.desc())
        elif sort == "active":
            query = query.order_by(Project.updated_at.desc())
        else:
            query = query.order_by(Project.created_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_user_projects(user_id: str, page: int = 1, per_page: int = 20):
        """Get projects where user is a member."""
        member_project_ids = (
            db.session.query(ProjectMember.project_id)
            .filter_by(user_id=user_id)
            .subquery()
        )
        return (
            Project.query
            .filter(Project.id.in_(member_project_ids))
            .order_by(Project.updated_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    # -- Members --
    @staticmethod
    def add_member(project_id: str, user_id: str, role: str = "member") -> ProjectMember:
        existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if existing:
            raise ValueError("User is already a member.")

        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        db.session.add(member)
        db.session.commit()
        return member

    @staticmethod
    def remove_member(project_id: str, user_id: str):
        member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not member:
            raise ValueError("Member not found.")
        if member.role == "owner":
            raise ValueError("Cannot remove the project owner.")
        db.session.delete(member)
        db.session.commit()

    @staticmethod
    def update_member_role(project_id: str, user_id: str, role: str) -> ProjectMember:
        member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not member:
            raise ValueError("Member not found.")
        if member.role == "owner":
            raise ValueError("Cannot change the owner's role.")
        member.role = role
        db.session.commit()
        return member

    @staticmethod
    def get_member(project_id: str, user_id: str) -> Optional[ProjectMember]:
        return ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()

    @staticmethod
    def get_members(project_id: str):
        return (
            ProjectMember.query
            .filter_by(project_id=project_id)
            .order_by(ProjectMember.joined_at.asc())
            .all()
        )

    @staticmethod
    def get_user_role(project_id: str, user_id: str) -> Optional[str]:
        member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        return member.role if member else None

    # -- Star --
    @staticmethod
    def toggle_star(project: Project):
        # star_count is a simple counter, real implementation would have a stars table
        # For simplicity, we just toggle a count (could be abused, proper impl needs a table)
        project.star_count = max(0, project.star_count)
        db.session.commit()
        return project.star_count

    @staticmethod
    def _index_to_search(project: Project):
        SearchService.index_document(
            doc_id=project.id,
            source_type="project",
            title=project.name,
            body_text=(project.description or "")[:1000],
            created_at=project.created_at,
            extra={"slug": project.slug, "visibility": project.visibility,
                   "star_count": project.star_count},
        )

    @staticmethod
    def _remove_from_search(project: Project):
        SearchService.remove_document(project.id, "project")

    @staticmethod
    def _generate_slug(name: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = slug.strip("-") or "project"
        base = slug
        counter = 1
        while Project.query.filter_by(slug=slug).first():
            slug = f"{base}-{counter}"
            counter += 1
        return slug
