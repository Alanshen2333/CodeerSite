from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    slug = fields.Str(dump_only=True)
    description = fields.Str(validate=validate.Length(max=500))
    color = fields.Str(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))
    usage_count = fields.Int(dump_only=True)
    created_at = fields.Str(dump_only=True)


class TagCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    description = fields.Str(validate=validate.Length(max=500))
    color = fields.Str(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))
