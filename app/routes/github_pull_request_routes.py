from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.github.github_pull_request import GitHubPullRequest
from app.models.github.github_repo import GitHubRepo

pr_bp = Blueprint("/", __name__)

@pr_bp.route("/<repo_id>/pulls", methods=["GET"])
@jwt_required()
def get_all_pull_requests(repo_id):
    user_id = get_jwt_identity()
    # repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    repo = GitHubRepo.objects(id=repo_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    prs = GitHubPullRequest.objects(repo=repo).order_by("-created_at")
    return jsonify([{
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "created_at": pr.created_at,
        "user_login": pr.user_login,
    } for pr in prs]), 200

@pr_bp.route("/<repo_id>/pull/<int:number>", methods=["GET"])
@jwt_required()
def get_pull_request(repo_id, number):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    pr = GitHubPullRequest.objects(repo=repo, number=number).first()
    if not pr:
        return jsonify({"msg": "Pull request not found"}), 404

    return jsonify({
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "head_ref": pr.head_ref,
        "base_ref": pr.base_ref,
        "user_login": pr.user_login,
        "created_at": pr.created_at,
        "merged_at": pr.merged_at,
        "commits": pr.commits,
        "files": pr.files,
        "reviews": pr.reviews
    }), 200

@pr_bp.route("/<repo_id>/pull/<int:number>/commits", methods=["GET"])
@jwt_required()
def get_pull_request_commits(repo_id, number):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    pr = GitHubPullRequest.objects(repo=repo, number=number).first()
    if not pr:
        return jsonify({"msg": "Pull request not found"}), 404

    return jsonify(pr.commits), 200

@pr_bp.route("/<repo_id>/pull/<int:number>/files", methods=["GET"])
@jwt_required()
def get_pull_request_files(repo_id, number):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    pr = GitHubPullRequest.objects(repo=repo, number=number).first()
    if not pr:
        return jsonify({"msg": "Pull request not found"}), 404

    return jsonify(pr.files), 200

@pr_bp.route("/<repo_id>/pull/<int:number>/reviews", methods=["GET"])
@jwt_required()
def get_pull_request_reviews(repo_id, number):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    pr = GitHubPullRequest.objects(repo=repo, number=number).first()
    if not pr:
        return jsonify({"msg": "Pull request not found"}), 404

    return jsonify(pr.reviews), 200