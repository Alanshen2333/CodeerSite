from marshmallow import Schema, fields, validate


class CommentSchema(Schema):
    id = fields.Str(dump_only=True)
    user_id = fields.Str(dump_only=True)
    user = fields.Dict(dump_only=True)
    body = fields.Str(required=True)
    target_type = fields.Str(required=True)
    target_id = fields.Str(required=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


class CommentCreateSchema(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    target_type = fields.Str(required=True, validate=validate.OneOf(["question", "answer", "issue"]))
    target_id = fields.Str(required=True)


class CommentUpdateSchema(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
