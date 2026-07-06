from marshmallow import Schema, fields, validate


class AnswerSchema(Schema):
    id = fields.Str(dump_only=True)
    question_id = fields.Str(required=True)
    author_id = fields.Str(dump_only=True)
    author = fields.Dict(dump_only=True)
    body = fields.Str(required=True)
    body_html = fields.Str(dump_only=True)
    vote_count = fields.Int(dump_only=True)
    is_accepted = fields.Bool(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class AnswerCreateSchema(Schema):
    question_id = fields.Str(required=True, validate=validate.Regexp(UUID_RE, error="Invalid question_id format."))
    body = fields.Str(required=True, validate=validate.Length(min=10))


class AnswerUpdateSchema(Schema):
    body = fields.Str(required=True, validate=validate.Length(min=10))
