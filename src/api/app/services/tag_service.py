import re
from typing import List, Optional
from app.extensions import db
from app.models.tag import Tag


class TagService:
    @staticmethod
    def get_or_create_tags(tag_names: List[str]) -> List[Tag]:
        """Get existing tags by name or create new ones. Returns the list of Tag objects."""
        tags = []
        for name in tag_names:
            name = name.strip().lower()
            if not name:
                continue
            # Try to find existing
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                # Generate a unique slug
                slug = TagService._slugify(name)
                # Ensure slug uniqueness
                base_slug = slug
                counter = 1
                while Tag.query.filter_by(slug=slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                tag = Tag(name=name, slug=slug)
                db.session.add(tag)
                db.session.flush()
            tags.append(tag)
        return tags

    @staticmethod
    def get_tags(sort_by: str = "popular", page: int = 1, per_page: int = 36):
        """Get paginated tags."""
        query = Tag.query
        if sort_by == "popular":
            query = query.order_by(Tag.usage_count.desc())
        elif sort_by == "name":
            query = query.order_by(Tag.name.asc())
        else:
            query = query.order_by(Tag.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def search_tags(q: str, limit: int = 10) -> List[Tag]:
        """Search tags by name prefix."""
        return (
            Tag.query.filter(Tag.name.ilike(f"{q}%"))
            .order_by(Tag.usage_count.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_tag_by_slug(slug: str) -> Optional[Tag]:
        return Tag.query.filter_by(slug=slug).first()

    @staticmethod
    def update_usage_counts(tag_ids: List[str]):
        """Recalculate usage_count for given tags based on question_tags."""
        from app.models.question import question_tags

        for tag_id in tag_ids:
            count = db.session.query(question_tags).filter_by(tag_id=tag_id).count()
            tag = db.session.get(Tag, tag_id)
            if tag:
                tag.usage_count = count

    @classmethod
    def create_tag(
        cls, name: str, description: str = None, color: str = "#1677ff"
    ) -> Tag:
        """创建新标签。名称查重，自动生成 slug。"""
        name = name.strip().lower()
        existing = Tag.query.filter_by(name=name).first()
        if existing:
            raise ValueError("Tag already exists.")
        slug = cls._slugify(name)
        tag = Tag(name=name, slug=slug, description=description, color=color)
        db.session.add(tag)
        db.session.commit()
        return tag

    @classmethod
    def _slugify(cls, name: str) -> str:
        """Convert tag name to URL-safe slug."""
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-") or "tag"
