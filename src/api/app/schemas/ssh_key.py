from marshmallow import Schema, fields, validate


class CreateSshKeySchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    public_key = fields.Str(required=True, validate=validate.Length(min=1))


class SshKeySchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str()
    key_type = fields.Str()
    fingerprint = fields.Str()
    gitea_key_id = fields.Str()
    sync_status = fields.Str()
    sync_error = fields.Str()
    last_used_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
