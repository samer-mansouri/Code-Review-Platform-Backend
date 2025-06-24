from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_mail import Mail

db = MongoEngine()
jwt = JWTManager()
ma = Marshmallow()
mail = Mail()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.token_blocklist import TokenBlocklist
    jti = jwt_payload["jti"]
    return TokenBlocklist.objects(jti=jti).first() is not None