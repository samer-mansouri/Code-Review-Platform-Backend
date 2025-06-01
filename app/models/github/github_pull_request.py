from app.extensions import db
from datetime import datetime

class GitHubPullRequest(db.Document):
    repo = db.ReferenceField('GitHubRepo', required=True, reverse_delete_rule=db.CASCADE)
    number = db.IntField(required=True)  # GitHub uses "number" instead of "iid"
    title = db.StringField()
    body = db.StringField()
    state = db.StringField()  # "open", "closed", "merged"
    mergeable = db.BooleanField()
    head_ref = db.StringField()  # Source branch
    base_ref = db.StringField()  # Target branch
    user_login = db.StringField()
    created_at = db.DateTimeField()
    merged_at = db.DateTimeField()
    closed_at = db.DateTimeField()
    
    commits = db.ListField(db.DictField())  # Commit details
    files = db.ListField(db.DictField())    # Changed files with diffs
    reviews = db.ListField(db.DictField())  # Review information
    
    meta = {
        'indexes': ['repo', 'number'],
        'unique_with': ['repo', 'number']
    }