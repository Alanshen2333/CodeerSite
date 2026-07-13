from marshmallow import Schema, fields, validate


class KanbanColumnCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))


class KanbanCardCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    issue_id = fields.Str()


class KanbanCardMoveSchema(Schema):
    column_id = fields.Str(required=True)
    position = fields.Int(required=True)

class KanbanReorderSchema(Schema):
    column_ids = fields.List(
        fields.Str(required=True),
        required=True,
        validate=validate.Length(min=1),
    )
