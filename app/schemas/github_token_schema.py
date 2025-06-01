from marshmallow import Schema, fields

class GitHubTokenSchema(Schema):
    id = fields.String(dump_only=True)
    user_id = fields.String(dump_only=True)
    name = fields.String(required=True)
    token = fields.String(required=True)  
    created_at = fields.DateTime(dump_only=True)