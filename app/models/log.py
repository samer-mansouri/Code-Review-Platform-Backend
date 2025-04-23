from app.extensions import db
from datetime import datetime

class Log(db.Document):
    user_id = db.StringField(required=True)
    action = db.StringField(required=True)
    details = db.StringField()
    timestamp = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'Logs',
        'ordering': ['-timestamp'],
        'indexes': ['user_id', 'action']
    }