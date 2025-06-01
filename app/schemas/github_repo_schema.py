from marshmallow import Schema, fields

class GitHubRepoSchema(Schema):
    id = fields.String(dump_only=True)
    name = fields.Str()
    full_name = fields.Str()
    owner_login = fields.Str()
    html_url = fields.Str()
    private = fields.Bool()
    repo_id = fields.Int()
    token_id = fields.String()
    created_at = fields.DateTime(dump_only=True)