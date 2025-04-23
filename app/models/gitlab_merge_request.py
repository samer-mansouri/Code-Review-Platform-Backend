from app.extensions import db
from datetime import datetime

class GitLabMergeRequest(db.Document):
    project = db.ReferenceField('GitLabProject', required=True, reverse_delete_rule=db.CASCADE)
    iid = db.IntField(required=True)
    title = db.StringField()
    description = db.StringField()
    state = db.StringField()
    merge_status = db.StringField()
    source_branch = db.StringField()
    target_branch = db.StringField()
    author = db.StringField()
    created_at = db.DateTimeField()
    merged_at = db.DateTimeField()

    commits = db.ListField(db.DictField())   # Each commit includes diffs
    diffs = db.ListField(db.DictField())     # Complete diff list
    approvals = db.DictField()               # Optional approval metadata

    meta = {
        'indexes': ['project', 'iid'],
        'unique_with': ['project', 'iid']
    }
