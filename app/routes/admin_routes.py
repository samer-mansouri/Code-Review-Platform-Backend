from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.utils.decorators import role_required
from app.schemas.user_schema import UserRegisterSchema
from werkzeug.exceptions import BadRequest
from app.utils.helpers import paginate_query, log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_developers():
    developers = User.objects(role="developer")

    result = [
        {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        } for user in developers
    ]

    log_action(get_jwt_identity(), 'list_developers', "Listed developers")
    return jsonify({"users": result})


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.delete()
    log_action(get_jwt_identity(), 'delete_user', f"Deleted user {user_id}")
    return jsonify({"msg": "User deleted successfully"})

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_user():
    data = request.get_json()
    schema = UserRegisterSchema()
    errors = schema.validate(data)
    if errors:
        raise BadRequest(errors)
    if User.objects(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 400

    role_value = data.get('role', 'developer')
    if role_value not in ['admin', 'developer']:
        return jsonify({"error": "Invalid role"}), 400

    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=role_value
    )
    user.set_password(data['password'])
    user.save()
    result = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "msg": "User created successfully"
    }
    log_action(get_jwt_identity(), 'create_user', f"Created user {user.email}")
    return jsonify(result), 201

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if 'role' in data and data['role'] not in ['admin', 'developer']:
        return jsonify({"error": "Invalid role"}), 400

    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.role = data.get("role", user.role)
    if 'password' in data:
        user.set_password(data['password'])
    user.save()
    log_action(get_jwt_identity(), 'update_user', f"Updated user {user_id}")
    result = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "msg": "User updated successfully"
    }
    return jsonify(result)

@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    result = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }
    log_action(get_jwt_identity(), 'get_user', f"Fetched user {user_id}")
    return jsonify(result)
