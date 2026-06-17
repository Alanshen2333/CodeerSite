from marshmallow import Schema, fields, validate


class ProjectCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=2000))
    visibility = fields.Str(validate=validate.OneOf(["public", "private"]))


class ProjectUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=2000))
    visibility = fields.Str(validate=validate.OneOf(["public", "private"]))
