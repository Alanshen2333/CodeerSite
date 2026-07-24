"""Repo schema."""

from marshmallow import Schema, fields


class RepoCreateSchema(Schema):
    """创建仓库请求体。name 默认使用 project slug。"""

    name = fields.String(
        load_default=None, validate=lambda x: len(x) <= 100 if x else True
    )
    description = fields.String(load_default=None)
    private = fields.Boolean(load_default=False)
