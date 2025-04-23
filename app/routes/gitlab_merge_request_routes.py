from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.gitlab_merge_request import GitLabMergeRequest
from app.models.gitlab_project import GitLabProject

mr_bp = Blueprint("gitlab_merge_request", __name__)

@mr_bp.route("/<project_id>/merge-requests", methods=["GET"])
@jwt_required()
def get_all_merge_requests(project_id):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    mrs = GitLabMergeRequest.objects(project=project).order_by("-created_at")
    return jsonify([{
        "iid": mr.iid,
        "title": mr.title,
        "state": mr.state,
        "merge_status": mr.merge_status,
        "created_at": mr.created_at,
    } for mr in mrs]), 200

@mr_bp.route("/<project_id>/merge-request/<int:iid>", methods=["GET"])
@jwt_required()
def get_merge_request(project_id, iid):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    mr = GitLabMergeRequest.objects(project=project, iid=iid).first()
    if not mr:
        return jsonify({"msg": "Merge request not found"}), 404

    return jsonify({
        "iid": mr.iid,
        "title": mr.title,
        "description": mr.description,
        "state": mr.state,
        "merge_status": mr.merge_status,
        "source_branch": mr.source_branch,
        "target_branch": mr.target_branch,
        "author": mr.author,
        "created_at": mr.created_at,
        "merged_at": mr.merged_at,
        "commits": mr.commits,
        "diffs": mr.diffs,
        "approvals": mr.approvals
    }), 200

@mr_bp.route("/<project_id>/merge-request/<int:iid>/commits", methods=["GET"])
@jwt_required()
def get_merge_request_commits(project_id, iid):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    mr = GitLabMergeRequest.objects(project=project, iid=iid).first()
    if not mr:
        return jsonify({"msg": "Merge request not found"}), 404

    return jsonify(mr.commits), 200

@mr_bp.route("/<project_id>/merge-request/<int:iid>/diffs", methods=["GET"])
@jwt_required()
def get_merge_request_diffs(project_id, iid):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    mr = GitLabMergeRequest.objects(project=project, iid=iid).first()
    if not mr:
        return jsonify({"msg": "Merge request not found"}), 404

    return jsonify(mr.diffs), 200

@mr_bp.route("/<project_id>/merge-request/<int:iid>/approvals", methods=["GET"])
@jwt_required()
def get_merge_request_approvals(project_id, iid):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    mr = GitLabMergeRequest.objects(project=project, iid=iid).first()
    if not mr:
        return jsonify({"msg": "Merge request not found"}), 404

    return jsonify(mr.approvals), 200
