from marshmallow import Schema, fields, validate


class BadgeSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    slug = fields.Str(dump_only=True)
    description = fields.Str(validate=validate.Length(max=500))
    icon = fields.Str(validate=validate.Length(max=20))
    color = fields.Str(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))
    kind = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


class BadgeCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    description = fields.Str(validate=validate.Length(max=500))
    icon = fields.Str(validate=validate.Length(max=20))
    color = fields.Str(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))


class BadgeUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=50))
    description = fields.Str(validate=validate.Length(max=500))
    icon = fields.Str(validate=validate.Length(max=20))
    color = fields.Str(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))


class AwardSchema(Schema):
    user_id = fields.Str(required=True, validate=validate.Length(min=1, max=36))
    reason = fields.Str(validate=validate.Length(max=500))


class RevokeSchema(Schema):
    user_id = fields.Str(required=True, validate=validate.Length(min=1, max=36))
