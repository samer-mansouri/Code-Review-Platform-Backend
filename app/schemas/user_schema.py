from app.extensions import ma
from marshmallow import fields, validate

class UserRegisterSchema(ma.Schema):
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(['admin', 'developer']), default='developer')

class UserLoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)