from app.extensions import db
from datetime import datetime

class GitHubCommit(db.Document):
    repo = db.ReferenceField('GitHubRepo', required=True, reverse_delete_rule=db.CASCADE)
    sha = db.StringField(required=True)
    message = db.StringField()
    author_name = db.StringField()
    author_login = db.StringField()
    created_at = db.DateTimeField()
    files = db.ListField(db.DictField())  # Contains diff information
    
    meta = {
        'indexes': ['repo', 'sha'],
        'unique_with': ['repo', 'sha']
    }