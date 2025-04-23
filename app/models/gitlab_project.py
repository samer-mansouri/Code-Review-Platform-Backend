from app.extensions import db
from datetime import datetime

class GitLabProject(db.Document):
    user_id = db.ReferenceField('User', required=True, reverse_delete_rule=db.CASCADE)
    token_id = db.ReferenceField('GitLabToken', required=True)
    project_id = db.IntField(required=True)
    name = db.StringField(required=True)
    path_with_namespace = db.StringField(required=True)
    web_url = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {'indexes': ['user_id', 'project_id'], 'strict': False}