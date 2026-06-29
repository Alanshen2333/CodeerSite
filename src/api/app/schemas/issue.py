from marshmallow import Schema, fields, validate


class IssueCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    body = fields.Str()
    assignee_id = fields.Str()
    priority = fields.Str(validate=validate.OneOf(["low", "medium", "high", "critical"]))
    milestone_id = fields.Str()
    tag_ids = fields.List(fields.Str())


class IssueUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=300))
    body = fields.Str()
    assignee_id = fields.Str(allow_none=True)
    status = fields.Str(validate=validate.OneOf(["open", "in_progress", "closed"]))
    priority = fields.Str(validate=validate.OneOf(["low", "medium", "high", "critical"]))
    milestone_id = fields.Str(allow_none=True)
    tag_ids = fields.List(fields.Str())
