from sqlalchemy import func
from app.extensions import db


class AtomicCounter:
    """原子递增/递减计数器，使用 SQL 表达式级更新，支持下限 clamp。

    生产环境使用 PostgreSQL 的 GREATEST 函数；不再为 SQLite 做兼容回退。
    """

    @staticmethod
    def adjust(
        model_class,
        pk: str,
        column: str,
        delta: int,
        min_value: int | None = 0,
    ) -> int:
        """对指定行、指定列做 delta 的原子加减，可选下限 clamp。

        返回实际更新的行数（正常为 1）。
        """
        if delta == 0:
            return 0

        col = getattr(model_class, column)
        expr = col + delta
        if min_value is not None:
            new_value = func.greatest(expr, min_value)
        else:
            new_value = expr

        return model_class.query.filter_by(id=pk).update(
            {column: new_value},
            synchronize_session=False,
        )

    @staticmethod
    def refresh(instance) -> None:
        """刷新 ORM 实例，使内存中的计数与数据库保持一致。"""
        db.session.refresh(instance)
