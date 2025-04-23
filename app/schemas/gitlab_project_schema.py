from marshmallow import Schema, fields

class GitLabProjectSchema(Schema):
    id = fields.String(dump_only=True)
    name = fields.Str()
    path_with_namespace = fields.Str()
    web_url = fields.Str()
    project_id = fields.Int()
    token_id = fields.String()
    created_at = fields.DateTime(dump_only=True)
