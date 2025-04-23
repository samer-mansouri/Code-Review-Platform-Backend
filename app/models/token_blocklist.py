from app.extensions import db
from datetime import datetime

class TokenBlocklist(db.Document):
    jti = db.StringField(required=True, unique=True)
    created_at = db.DateTimeField(default=datetime.utcnow)