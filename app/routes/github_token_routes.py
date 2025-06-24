from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.github.github_token import GitHubToken
from app.models.user import User
from app.schemas.github_token_schema import GitHubTokenSchema
from app.utils.helpers import is_github_token_valid

github_token_bp = Blueprint('github_token', __name__)
schema = GitHubTokenSchema()

@github_token_bp.route('/', methods=['POST'])
@jwt_required()
def add_github_token():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get("name") or not data.get("token"):
        return jsonify({"msg": "Missing name or token"}), 400

    if not is_github_token_valid(data["token"]):
        return jsonify({"msg": "Invalid GitHub token"}), 400

    if GitHubToken.objects(user_id=user_id, name=data["name"]).first():
        return jsonify({"msg": "Token name already exists"}), 400

    token = GitHubToken(user_id=user_id, name=data["name"], token=data["token"])
    token.save()

    return jsonify({"msg": "Token added", "id": str(token.id)}), 201

@github_token_bp.route('/', methods=['GET'])
@jwt_required()
def get_github_tokens():
    user_id = get_jwt_identity()
    tokens = GitHubToken.objects(user_id=user_id)
    return jsonify(GitHubTokenSchema(many=True).dump(tokens)), 200

@github_token_bp.route('/<token_id>', methods=['DELETE'])
@jwt_required()
def delete_github_token(token_id):
    user_id = get_jwt_identity()
    token = GitHubToken.objects(id=token_id, user_id=user_id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    token.delete()
    return jsonify({"msg": "Token deleted"}), 200