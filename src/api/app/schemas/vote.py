from marshmallow import Schema, fields, validate


class VoteCreateSchema(Schema):
    vote_type = fields.Str(required=True, validate=validate.OneOf(["up", "down"]))
    target_type = fields.Str(required=True, validate=validate.OneOf(["question", "answer"]))
    target_id = fields.Str(required=True)
