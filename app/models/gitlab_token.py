from app.extensions import db
from datetime import datetime

class GitLabToken(db.Document):
    user_id = db.ReferenceField('User', required=True, reverse_delete_rule=db.CASCADE)
    name = db.StringField(required=True)
    token = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    meta = {
        'indexes': ['user_id', 'name'],
        'strict': False
    }
