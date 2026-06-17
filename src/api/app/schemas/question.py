from marshmallow import Schema, fields, validate


class QuestionSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=5, max=300))
    body = fields.Str(required=True)
    body_html = fields.Str(dump_only=True)
    author_id = fields.Str(dump_only=True)
    author = fields.Dict(dump_only=True)
    tags = fields.List(fields.Dict(), dump_only=True)
    vote_count = fields.Int(dump_only=True)
    answer_count = fields.Int(dump_only=True)
    view_count = fields.Int(dump_only=True)
    accepted_answer_id = fields.Str(dump_only=True)
    is_closed = fields.Bool(dump_only=True)
    is_pinned = fields.Bool(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


class QuestionCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=5, max=300))
    body = fields.Str(required=True, validate=validate.Length(min=10))
    tag_ids = fields.List(fields.Str(), validate=validate.Length(max=5))


class QuestionUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=5, max=300))
    body = fields.Str(validate=validate.Length(min=10))
    tag_ids = fields.List(fields.Str(), validate=validate.Length(max=5))
