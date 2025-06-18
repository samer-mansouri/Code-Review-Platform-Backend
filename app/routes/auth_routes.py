from flask import Blueprint, request, jsonify
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from app.services.auth_service import AuthService
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
    unset_jwt_cookies,
    create_access_token
)
from app.models.token_blocklist import TokenBlocklist
from app.utils.helpers import log_action
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    file = request.files.get('profile_picture')

    schema = UserRegisterSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Default role is 'developer' if not provided
    data['role'] = data.get('role', 'developer')
    if data['role'] not in ['admin', 'developer']:
        return jsonify({'error': 'Invalid role'}), 400

    user, err = AuthService.register(data, file)
    if err:
        return jsonify({'error': err}), 400

    return jsonify({"msg": "User created", "user_id": str(user.id)})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    schema = UserLoginSchema()
    errors = schema.validate(data)
    if errors:
        return jsonify(errors), 400

    access, refresh, user = AuthService.authenticate(data['email'], data['password'])
    if not access:
        log_action("anonymous", "failed_login", f"Failed login attempt for {data['email']}")
        return jsonify({"msg": "Invalid credentials"}), 401

    log_action(user.id, "login", f"User {user.email} logged in")
    return jsonify({
        "access_token": access,
        "refresh_token": refresh,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    })

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"msg": "Protected route", "user": current_user})

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    current_user_id = get_jwt_identity()
    TokenBlocklist(jti=jti).save()
    log_action(current_user_id, "logout", f"User {current_user_id} logged out")
    response = jsonify({"msg": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    user, err = AuthService.update_profile(current_user_id, data)
    if err:
        return jsonify({"error": err}), 404
    return jsonify({
        "msg": "Profile updated",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }
    })

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    success, err = AuthService.change_password(current_user_id, old_password, new_password)
    if not success:
        return jsonify({"error": err}), 400
    return jsonify({"msg": "Password changed successfully"})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }), 200
