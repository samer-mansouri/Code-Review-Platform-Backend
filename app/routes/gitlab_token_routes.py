from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.gitlab_token import GitLabToken
from app.models.user import User
from app.schemas.gitlab_token_schema import GitLabTokenSchema
from app.utils.helpers import is_gitlab_token_valid

gitlab_token_bp = Blueprint('gitlab_token', __name__)
schema = GitLabTokenSchema()

@gitlab_token_bp.route('/', methods=['POST'])
@jwt_required()
def add_gitlab_token():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("name") or not data.get("token"):
        return jsonify({"msg": "Missing name or token"}), 400

    if not is_gitlab_token_valid(data["token"]):
        return jsonify({"msg": "Invalid GitLab token"}), 400

    if GitLabToken.objects(user_id=user_id, name=data["name"]).first():
        return jsonify({"msg": "Token name already exists"}), 400

    token = GitLabToken(user_id=user_id, name=data["name"], token=data["token"])
    token.save()

    return jsonify({"msg": "Token added", "id": str(token.id)}), 201

@gitlab_token_bp.route('/', methods=['GET'])
@jwt_required()
def get_gitlab_tokens():
    user_id = get_jwt_identity()
    tokens = GitLabToken.objects(user_id=user_id)
    print(jsonify(GitLabTokenSchema(many=True).dump(tokens)))
    return jsonify(GitLabTokenSchema(many=True).dump(tokens)), 200

@gitlab_token_bp.route('/<token_id>', methods=['DELETE'])
@jwt_required()
def delete_gitlab_token(token_id):
    user_id = get_jwt_identity()
    token = GitLabToken.objects(id=token_id, user_id=user_id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    token.delete()
    return jsonify({"msg": "Token deleted"}), 200
