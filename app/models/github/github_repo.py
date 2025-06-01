from app.extensions import db
from datetime import datetime

class GitHubRepo(db.Document):
    user_id = db.ReferenceField('User', required=True, reverse_delete_rule=db.CASCADE)
    token_id = db.ReferenceField('GitHubToken', required=True)
    repo_id = db.IntField(required=True)
    name = db.StringField(required=True)
    full_name = db.StringField(required=True)  # "owner/repo-name"
    owner_login = db.StringField(required=True)
    html_url = db.StringField()
    private = db.BooleanField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': ['user_id', 'repo_id', 'full_name'],
        'strict': False
    }