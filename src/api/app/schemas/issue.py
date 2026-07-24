from marshmallow import Schema, fields, validate


class IssueCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    body = fields.Str()
    assignee_id = fields.Str()
    priority = fields.Str(
        validate=validate.OneOf(["low", "medium", "high", "critical"])
    )
    milestone_id = fields.Str()
    tag_ids = fields.List(fields.Str())
    # 预估工时（秒），可为空表示未估时
    time_estimate = fields.Int(allow_none=True, validate=validate.Range(min=0))


class IssueUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=300))
    body = fields.Str()
    assignee_id = fields.Str(allow_none=True)
    status = fields.Str(validate=validate.OneOf(["open", "in_progress", "closed"]))
    priority = fields.Str(
        validate=validate.OneOf(["low", "medium", "high", "critical"])
    )
    milestone_id = fields.Str(allow_none=True)
    tag_ids = fields.List(fields.Str())
    # 预估工时（秒），allow_none 以支持清空估时
    time_estimate = fields.Int(allow_none=True, validate=validate.Range(min=0))


class TimeEntryCreateSchema(Schema):
    # 本次耗时（秒），正整数
    seconds = fields.Int(required=True, validate=validate.Range(min=1))
    note = fields.Str(validate=validate.Length(max=500))
