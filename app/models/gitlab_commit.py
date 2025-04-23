from app.extensions import db
from datetime import datetime

class GitLabCommit(db.Document):
    project = db.ReferenceField('GitLabProject', required=True, reverse_delete_rule=db.CASCADE)
    sha = db.StringField(required=True)
    title = db.StringField()
    author_name = db.StringField()
    created_at = db.DateTimeField()
    diffs = db.ListField(db.DictField())  # List of diff objects (old_path, new_path, diff)

    meta = {
        'indexes': ['project', 'sha'],
        'unique_with': ['project', 'sha']
    }
