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
from app.utils.token import verify_reset_token
import os
from werkzeug.utils import secure_filename
from flask import current_app, url_for
from datetime import datetime


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
    profile_picture_url = (
    url_for('uploaded_file', filename=user.profile_picture, _external=True)
    if user.profile_picture else None
    )
    return jsonify({
        "access_token": access,
        "refresh_token": refresh,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_picture": profile_picture_url
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
    
    profile_picture_url = (
    url_for('uploaded_file', filename=user.profile_picture, _external=True)
    if user.profile_picture else None
    )
    return jsonify({
        "msg": "Profile updated",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "profile_picture": profile_picture_url
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
    
    profile_picture_url = (
    url_for('uploaded_file', filename=user.profile_picture, _external=True)
    if user.profile_picture else None
    )

    return jsonify({
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "profile_picture": profile_picture_url
    }), 200


@auth_bp.route('/request-reset', methods=['POST'])
def request_reset():
    data = request.get_json()
    email = data.get('email')
    user = User.objects(email=email).first()
    if user:
        AuthService.send_reset_email(user)
    return jsonify(message="If your email exists, you will receive a reset link"), 200

@auth_bp.route('/reset/<token>', methods=['POST'])
def reset_password_token(token):
    email = verify_reset_token(token)
    if not email:
        return jsonify(message="Invalid or expired token"), 400
    data = request.get_json()
    new_password = data.get('password')
    user = User.objects(email=email).first()
    if user:
        user.set_password(new_password)
        user.save()
        return jsonify(message="Password updated successfully"), 200
    return jsonify(message="User not found"), 404


@auth_bp.route('/update-profile-picture', methods=['PUT'])
@jwt_required()
def update_profile_picture():
    current_user_id = get_jwt_identity()
    user = User.objects(id=current_user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    from app.utils.helpers import allowed_file
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    user.profile_picture = filename
    user.updated_at = datetime.utcnow()
    user.save()

    return jsonify({
        "msg": "Profile picture updated",
        "profile_picture": filename
    }), 200