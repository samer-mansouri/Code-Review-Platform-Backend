from flask_jwt_extended import get_jwt_identity
from functools import wraps
from flask import jsonify
from app.models.user import User

def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            user = User.objects(id=get_jwt_identity()).first()
            if not user or user.role != role:
                return jsonify({"msg": "Unauthorized"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper