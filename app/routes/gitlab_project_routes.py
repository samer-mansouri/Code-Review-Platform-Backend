from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.gitlab_token import GitLabToken
from app.models.gitlab_project import GitLabProject
from app.schemas.gitlab_project_schema import GitLabProjectSchema
from app.utils.helpers import get_gitlab_project_by_url, get_gitlab_commits_with_diffs, get_gitlab_merge_requests_with_commits_and_diffs, get_gitlab_mr_full_info, get_all_gitlab_merge_requests_full
from app.models.gitlab_commit import GitLabCommit
from app.models.gitlab_merge_request import GitLabMergeRequest

gitlab_project_bp = Blueprint("gitlab_project", __name__)

@gitlab_project_bp.route("/", methods=["POST"])
@jwt_required()
def add_gitlab_project():
    user_id = get_jwt_identity()
    data = request.get_json()

    project_url = data.get("project_url")
    token_id = data.get("token_id")

    if not project_url or not token_id:
        return jsonify({"msg": "Missing project URL or token ID"}), 400

    token_obj = GitLabToken.objects(id=token_id, user_id=user_id).first()
    if not token_obj:
        return jsonify({"msg": "Invalid token"}), 404

    project_data, error = get_gitlab_project_by_url(project_url, token_obj.token)
    if error:
        return jsonify({"msg": error}), 400

    existing = GitLabProject.objects(user_id=user_id, project_id=project_data["id"]).first()
    if existing:
        return jsonify({"msg": "Project already added"}), 409

    project = GitLabProject(
        user_id=user_id,
        token_id=token_obj.id,
        project_id=project_data["id"],
        name=project_data["name"],
        path_with_namespace=project_data["path_with_namespace"],
        web_url=project_data["web_url"]
    )
    project.save()

    return jsonify(GitLabProjectSchema().dump(project)), 201

@gitlab_project_bp.route("/<project_id>/commits/save", methods=["POST"])
@jwt_required()
def fetch_and_store_commits(project_id):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    token = GitLabToken.objects(id=project.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    commits, error = get_gitlab_commits_with_diffs(project.project_id, token.token, limit=10)
    if error:
        return jsonify({"msg": error}), 400

    stored_commits = []
    for c in commits:
        if "error" in c:
            continue

        existing = GitLabCommit.objects(project=project, sha=c["sha"]).first()
        if existing:
            continue  # Avoid duplicates

        commit = GitLabCommit(
            project=project,
            sha=c["sha"],
            title=c["title"],
            author_name=c["author_name"],
            created_at=c["created_at"],
            diffs=c["diffs"]
        )
        commit.save()
        stored_commits.append({
            "sha": c["sha"],
            "title": c["title"],
            "created_at": c["created_at"]
        })

    return jsonify({
        "msg": f"{len(stored_commits)} commits saved",
        "commits": stored_commits
    }), 201


@gitlab_project_bp.route("/<project_id>/merge-requests/save", methods=["POST"])
@jwt_required()
def fetch_and_store_mrs_with_commits_diffs(project_id):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    token = GitLabToken.objects(id=project.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    mrs, error = get_gitlab_merge_requests_with_commits_and_diffs(project.project_id, token.token)
    if error:
        return jsonify({"msg": error}), 400

    stored = []
    for mr in mrs:
        if "error" in mr:
            continue

        if GitLabMergeRequest.objects(project=project, iid=mr["iid"]).first():
            continue

        GitLabMergeRequest(
            project=project,
            iid=mr["iid"],
            title=mr["title"],
            description=mr["description"],
            state=mr["state"],
            created_at=mr["created_at"],
            merged_at=mr["merged_at"],
            source_branch=mr["source_branch"],
            target_branch=mr["target_branch"],
            author=mr["author"],
            commits=mr["commits"]
        ).save()

        stored.append({
            "iid": mr["iid"],
            "title": mr["title"],
            "commits_count": len(mr["commits"])
        })

    return jsonify({"msg": f"{len(stored)} merge requests saved", "merge_requests": stored}), 201


@gitlab_project_bp.route("/<project_id>/merge-request/<int:iid>/save", methods=["POST"])
@jwt_required()
def fetch_and_save_full_mr(project_id, iid):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    token = GitLabToken.objects(id=project.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    mr_data, error = get_gitlab_mr_full_info(project.project_id, token.token, iid)
    if error:
        return jsonify({"msg": error}), 400

    existing = GitLabMergeRequest.objects(project=project, iid=iid).first()
    if existing:
        existing.update(**mr_data)
        msg = "updated"
    else:
        GitLabMergeRequest(project=project, **mr_data).save()
        msg = "created"

    return jsonify({
        "msg": f"Merge request {iid} {msg} successfully",
        "merge_request": {
            "iid": mr_data["iid"],
            "title": mr_data["title"],
            "merge_status": mr_data["merge_status"],
            "commits_count": len(mr_data["commits"]),
            "diffs_count": len(mr_data["diffs"]),
        }
    }), 201


@gitlab_project_bp.route("/<project_id>/merge-requests/full/save", methods=["POST"])
@jwt_required()
def fetch_and_store_all_merge_requests_full(project_id):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    token = GitLabToken.objects(id=project.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    full_mrs, error = get_all_gitlab_merge_requests_full(project.project_id, token.token)
    if error:
        return jsonify({"msg": error}), 400

    saved = []
    errors = []

    for mr_data in full_mrs:
        if "error" in mr_data:
            errors.append({"iid": mr_data.get("iid"), "error": mr_data["error"]})
            continue

        existing = GitLabMergeRequest.objects(project=project, iid=mr_data["iid"]).first()
        if existing:
            existing.update(**mr_data)
            action = "updated"
        else:
            GitLabMergeRequest(project=project, **mr_data).save()
            action = "created"

        saved.append({
            "iid": mr_data["iid"],
            "title": mr_data["title"],
            "merge_status": mr_data["merge_status"],
            "commits_count": len(mr_data["commits"]),
            "diffs_count": len(mr_data["diffs"]),
            "action": action
        })

    return jsonify({
        "saved_count": len(saved),
        "errors_count": len(errors),
        "saved": saved,
        "errors": errors
    }), 201


@gitlab_project_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_gitlab_projects():
    projects = GitLabProject.objects()
    return jsonify(GitLabProjectSchema(many=True).dump(projects)), 200

@gitlab_project_bp.route("/<project_id>/sync", methods=["POST"])
@jwt_required()
def sync_gitlab_project(project_id):
    user_id = get_jwt_identity()
    project = GitLabProject.objects(id=project_id).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    token = GitLabToken.objects(id=project.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    # Sync commits
    commits, commits_error = get_gitlab_commits_with_diffs(project.project_id, token.token, limit=10)
    stored_commits = []

    if not commits_error:
        for c in commits:
            if "error" in c:
                continue
            if GitLabCommit.objects(project=project, sha=c["sha"]).first():
                continue
            GitLabCommit(
                project=project,
                sha=c["sha"],
                title=c["title"],
                author_name=c["author_name"],
                created_at=c["created_at"],
                diffs=c["diffs"]
            ).save()
            stored_commits.append(c["sha"])
    
    # Sync MRs
    mrs, mrs_error = get_gitlab_merge_requests_with_commits_and_diffs(project.project_id, token.token)
    stored_mrs = []

    if not mrs_error:
        for mr in mrs:
            if "error" in mr:
                continue
            if GitLabMergeRequest.objects(project=project, iid=mr["iid"]).first():
                continue
            GitLabMergeRequest(
                project=project,
                iid=mr["iid"],
                title=mr["title"],
                description=mr["description"],
                state=mr["state"],
                created_at=mr["created_at"],
                merged_at=mr["merged_at"],
                source_branch=mr["source_branch"],
                target_branch=mr["target_branch"],
                author=mr["author"],
                commits=mr["commits"]
            ).save()
            stored_mrs.append(mr["iid"])

    return jsonify({
        "msg": "Sync completed",
        "commits_saved": len(stored_commits),
        "merge_requests_saved": len(stored_mrs),
        "commit_errors": bool(commits_error),
        "mr_errors": bool(mrs_error),
    }), 200


@gitlab_project_bp.route("/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_gitlab_project(project_id):
    user_id = get_jwt_identity()

    project = GitLabProject.objects(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"msg": "Projet introuvable"}), 404

    project.delete()  # Cascades to commits and MRs

    return jsonify({"msg": "Projet supprimé avec succès avec ses commits et MRs"}), 200
