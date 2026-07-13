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
    avatar_url = fields.Str(validate=validate.Length(max=500))


class ChangePasswordSchema(Schema):
    verification_code = fields.Str(required=True, validate=validate.Length(equal=6))
    new_password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128),
    )


class RequestEmailCodeSchema(Schema):
    purpose = fields.Str(
        required=True,
        validate=validate.OneOf(["change_password", "disable_2fa", "recover_2fa"]),
    )


class OAuthAuthorizeSchema(Schema):
    intent = fields.Str(
        required=True,
        validate=validate.OneOf(["bind", "login"]),
    )


class OAuthCallbackSchema(Schema):
    code = fields.Str(required=True)
    state = fields.Str(required=True)

class AdminUserUpdateSchema(Schema):
    """Admin 更新用户时的字段白名单校验。"""
    role = fields.Str(
        validate=validate.OneOf(["user", "moderator", "admin"]),
        load_default=None,
    )
    is_active = fields.Boolean(load_default=None)
