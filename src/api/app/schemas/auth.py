from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128),
    )
    display_name = fields.Str(validate=validate.Length(max=100))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=128),
    )


class UpdateProfileSchema(Schema):
    display_name = fields.Str(validate=validate.Length(max=100))
    bio = fields.Str(validate=validate.Length(max=500))
    website = fields.Str(validate=validate.Length(max=255))
    location = fields.Str(validate=validate.Length(max=100))
