from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.github.github_token import GitHubToken
from app.models.github.github_repo import GitHubRepo
from app.schemas.github_repo_schema import GitHubRepoSchema
from app.utils.helpers import get_github_project_by_url, get_github_commits_with_diffs, get_github_pull_requests_with_commits_and_diffs, get_github_pr_full_info, get_all_github_pull_requests_full
from app.models.github.github_commit import GitHubCommit
from app.models.github.github_pull_request import GitHubPullRequest

github_repo_bp = Blueprint("github_repo", __name__)

@github_repo_bp.route("/", methods=["POST"])
@jwt_required()
def add_github_repo():
    user_id = get_jwt_identity()
    data = request.get_json()

    repo_url = data.get("repo_url")
    token_id = data.get("token_id")

    if not repo_url or not token_id:
        return jsonify({"msg": "Missing repository URL or token ID"}), 400

    token_obj = GitHubToken.objects(id=token_id, user_id=user_id).first()
    if not token_obj:
        return jsonify({"msg": "Invalid token"}), 404

    repo_data, error = get_github_project_by_url(repo_url, token_obj.token)
    if error:
        return jsonify({"msg": error}), 400

    existing = GitHubRepo.objects(user_id=user_id, repo_id=repo_data["id"]).first()
    if existing:
        return jsonify({"msg": "Repository already added"}), 409

    repo = GitHubRepo(
        user_id=user_id,
        token_id=token_obj.id,
        repo_id=repo_data["id"],
        name=repo_data["name"],
        full_name=repo_data["full_name"],
        owner_login=repo_data["owner"]["login"],
        html_url=repo_data["html_url"],
        private=repo_data["private"]
    )
    repo.save()

    return jsonify(GitHubRepoSchema().dump(repo)), 201

@github_repo_bp.route("/<repo_id>/commits/save", methods=["POST"])
@jwt_required()
def fetch_and_store_commits(repo_id):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    token = GitHubToken.objects(id=repo.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    commits, error = get_github_commits_with_diffs(repo.owner_login, repo.name, token.token, limit=10)
    if error:
        return jsonify({"msg": error}), 400

    stored_commits = []
    for c in commits:
        if "error" in c:
            continue

        existing = GitHubCommit.objects(repo=repo, sha=c["sha"]).first()
        if existing:
            continue  # Avoid duplicates

        commit = GitHubCommit(
            repo=repo,
            sha=c["sha"],
            message=c["commit"]["message"].split("\n")[0],
            author_name=c["commit"]["author"]["name"],
            author_login=c["author"]["login"] if c.get("author") else None,
            created_at=c["commit"]["author"]["date"],
            files=c.get("files", [])
        )
        commit.save()
        stored_commits.append({
            "sha": c["sha"],
            "message": commit.message,
            "created_at": commit.created_at
        })

    return jsonify({
        "msg": f"{len(stored_commits)} commits saved",
        "commits": stored_commits
    }), 201

@github_repo_bp.route("/<repo_id>/pull-requests/save", methods=["POST"])
@jwt_required()
def fetch_and_store_prs_with_commits_diffs(repo_id):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    token = GitHubToken.objects(id=repo.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    prs, error = get_github_pull_requests_with_commits_and_diffs(repo.owner_login, repo.name, token.token)


    for pr in prs:
        print("pr user", pr.get('user'))
        print("type of pr['user']:", type(pr.get('user')))
    if error:
        return jsonify({"msg": error}), 400

    stored = []
    for pr in prs:
        if "error" in pr:
            continue

        if GitHubPullRequest.objects(repo=repo, number=pr["number"]).first():
            continue

        GitHubPullRequest(
            repo=repo,
            number=pr["number"],
            title=pr["title"],
            body=pr["body"],
            state=pr["state"],
            created_at=pr["created_at"],
            merged_at=pr["merged_at"],
            head_ref=pr["head"]["ref"],
            base_ref=pr["base"]["ref"],
            user_login=pr["user"],
            commits=pr["commits"]
        ).save()

        stored.append({
            "number": pr["number"],
            "title": pr["title"],
            "commits_count": len(pr["commits"])
        })

    return jsonify({"msg": f"{len(stored)} pull requests saved", "pull_requests": stored}), 201

@github_repo_bp.route("/<repo_id>/pull-request/<int:number>/save", methods=["POST"])
@jwt_required()
def fetch_and_save_full_pr(repo_id, number):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    token = GitHubToken.objects(id=repo.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    pr_data, error = get_github_pr_full_info(repo.owner_login, repo.name, token.token, number)

    if error:
        return jsonify({"msg": error}), 400


    existing = GitHubPullRequest.objects(repo=repo, number=number).first()
    if existing:
        existing.update(**pr_data)
        msg = "updated"
    else:
        print("before")
        GitHubPullRequest(repo=repo, **pr_data).save()
        print("after")
        msg = "created"

    return jsonify({
        "msg": f"Pull request {number} {msg} successfully",
        "pull_request": {
            "number": pr_data["number"],
            "title": pr_data["title"],
            "commits_count": len(pr_data["commits"]),
            "files_count": len(pr_data["files"]),
            "review_comments_count": len(pr_data["reviews"]),
        }
    }), 201

@github_repo_bp.route("/<repo_id>/pull-requests/full/save", methods=["POST"])
@jwt_required()
def fetch_and_store_all_pull_requests_full(repo_id):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    token = GitHubToken.objects(id=repo.token_id.id).first()
    if not token:
        return jsonify({"msg": "Token not found"}), 404

    full_prs, error = get_all_github_pull_requests_full(repo.owner_login, repo.name, token.token)
    if error:
        return jsonify({"msg": error}), 400

    saved = []
    errors = []

    for pr_data in full_prs:
        if "error" in pr_data:
            errors.append({"number": pr_data.get("number"), "error": pr_data["error"]})
            continue

        existing = GitHubPullRequest.objects(repo=repo, number=pr_data["number"]).first()
        if existing:
            existing.update(**pr_data)
            action = "updated"
        else:
            GitHubPullRequest(repo=repo, **pr_data).save()
            action = "created"

        saved.append({
            "number": pr_data["number"],
            "title": pr_data["title"],
            "commits_count": len(pr_data["commits"]),
            "files_count": len(pr_data["files"]),
            "action": action
        })

    return jsonify({
        "saved_count": len(saved),
        "errors_count": len(errors),
        "saved": saved,
        "errors": errors
    }), 201


@github_repo_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_github_repos():
    repos = GitHubRepo.objects()
    return jsonify(GitHubRepoSchema(many=True).dump(repos)), 200


@github_repo_bp.route("/<repo_id>/pulls", methods=["GET"])
@jwt_required()
def get_pull_requests_for_repo(repo_id):
    user_id = get_jwt_identity()
    repo = GitHubRepo.objects(id=repo_id, user_id=user_id).first()

    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    prs = GitHubPullRequest.objects(repo=repo).order_by("-created_at")

    result = []
    for pr in prs:
        result.append({
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "created_at": pr.created_at,
            "user_login": pr.user_login,
        })

    return jsonify(result), 200

@github_repo_bp.route("/<repo_id>/pull/<int:number>", methods=["GET"])
@jwt_required()
def get_pull_request_details(repo_id, number):
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
        "body": pr.body,
        "commits": pr.commits,
        "files": pr.files,
        "reviews": pr.reviews,
    }), 200
