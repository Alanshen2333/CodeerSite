from marshmallow import Schema, fields, validate


class AddMemberSchema(Schema):
    user_id = fields.Str(required=True)
    role = fields.Str(validate=validate.OneOf(["admin", "member"]))


class UpdateMemberSchema(Schema):
    role = fields.Str(required=True, validate=validate.OneOf(["admin", "member"]))
