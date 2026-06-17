from marshmallow import Schema, fields, validate


class MilestoneCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str()
    due_date = fields.Date()


class MilestoneUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str()
    due_date = fields.Date(allow_none=True)
    status = fields.Str(validate=validate.OneOf(["open", "closed"]))
