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
def list_users():
    role_filter = request.args.get('role')
    email_filter = request.args.get('email')

    query = User.objects
    if role_filter:
        query = query.filter(role=role_filter)
    if email_filter:
        query = query.filter(email__icontains=email_filter)

    # paginated = paginate_query(query, request)
    result = [
        {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        } for user in query
    ]
    log_action(get_jwt_identity(), 'list_users', f"Listed users")
    # return jsonify({"total": paginated['total'], "page": paginated['page'], "limit": paginated['limit'], "users": result})

    return jsonify({ "users": result})

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
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    user.save()
    log_action(get_jwt_identity(), 'create_user', f"Created user {user.email}")
    return jsonify({"msg": "User created", "id": str(user.id)}), 201

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.role = data.get("role", user.role)
    if 'password' in data:
        user.set_password(data['password'])
    user.save()
    log_action(get_jwt_identity(), 'update_user', f"Updated user {user_id}")
    return jsonify({"msg": "User updated", "id": str(user.id)})