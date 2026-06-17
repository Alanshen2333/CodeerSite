from marshmallow import Schema, fields, validate


class BookmarkCreateSchema(Schema):
    target_type = fields.Str(required=True, validate=validate.OneOf(["question", "project"]))
    target_id = fields.Str(required=True)
