from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.github.github_repo import GitHubRepo
from app.models.github.github_pull_request import GitHubPullRequest
from app.models.gitlab_project import GitLabProject
from app.models.gitlab_merge_request import GitLabMergeRequest

stats_bp = Blueprint("stats", __name__)


# Helpers to normalize states

def get_gitlab_status(mr):
    if mr.state == "merged":
        return "merged"
    elif mr.state == "closed":
        return "closed"
    elif mr.merge_status == "cannot_be_merged":
        return "conflict"
    else:
        return "open"


def get_github_status(pr):
    if pr.merged_at:
        return "merged"
    elif pr.state == "closed":
        return "closed"
    elif hasattr(pr, "mergeable") and pr.mergeable is False:
        return "conflict"
    else:
        return "open"


@stats_bp.route("/overview", methods=["GET"])
@jwt_required()
def get_stats_overview():
    user_id = get_jwt_identity()

    # GitHub
    github_repos = GitHubRepo.objects()
    github_repo_ids = [r.id for r in github_repos]
    github_prs = GitHubPullRequest.objects(repo__in=github_repo_ids)

    github_merged = sum(1 for pr in github_prs if pr.merged_at)

    # GitLab
    gitlab_projects = GitLabProject.objects()
    gitlab_project_ids = [p.id for p in gitlab_projects]
    gitlab_mrs = GitLabMergeRequest.objects(project__in=gitlab_project_ids)

    gitlab_merged = sum(1 for mr in gitlab_mrs if mr.state == "merged")

    return jsonify({
        "github": {
            "repo_count": len(github_repos),
            "pull_request_count": len(github_prs),
            "merged_pr_count": github_merged,
            "merge_rate": round((github_merged / len(github_prs)) * 100, 2) if github_prs else 0
        },
        "gitlab": {
            "project_count": len(gitlab_projects),
            "merge_request_count": len(gitlab_mrs),
            "merged_mr_count": gitlab_merged,
            "merge_rate": round((gitlab_merged / len(gitlab_mrs)) * 100, 2) if gitlab_mrs else 0
        }
    }), 200


@stats_bp.route("/github/pull-requests/monthly", methods=["GET"])
@jwt_required()
def github_prs_per_month():
    user_id = get_jwt_identity()
    repos = GitHubRepo.objects().only("id")
    repo_ids = [r.id for r in repos]

    pipeline = [
        {"$match": {"repo": {"$in": repo_ids}, "created_at": {"$ne": None}}},
        {"$group": {
            "_id": {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]

    results = list(GitHubPullRequest.objects.aggregate(*pipeline))
    data = [
        {
            "month": f"{r['_id']['year']}-{str(r['_id']['month']).zfill(2)}",
            "count": r["count"]
        }
        for r in results
    ]
    return jsonify(data), 200


@stats_bp.route("/gitlab/merge-requests/monthly", methods=["GET"])
@jwt_required()
def gitlab_mrs_per_month():
    user_id = get_jwt_identity()
    projects = GitLabProject.objects().only("id")
    project_ids = [p.id for p in projects]

    pipeline = [
        {"$match": {"project": {"$in": project_ids}, "created_at": {"$ne": None}}},
        {"$group": {
            "_id": {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]

    results = list(GitLabMergeRequest.objects.aggregate(*pipeline))
    data = [
        {
            "month": f"{r['_id']['year']}-{str(r['_id']['month']).zfill(2)}",
            "count": r["count"]
        }
        for r in results
    ]
    return jsonify(data), 200


@stats_bp.route("/github/merge-ratio", methods=["GET"])
@jwt_required()
def github_merge_ratio():
    user_id = get_jwt_identity()
    repo_ids = [r.id for r in GitHubRepo.objects()]
    prs = GitHubPullRequest.objects(repo__in=repo_ids)

    merged = sum(1 for pr in prs if pr.merged_at)
    closed = sum(1 for pr in prs if pr.state == "closed" and not pr.merged_at)
    open_ = len(prs) - merged - closed

    return jsonify({
        "merged": merged,
        "closed": closed,
        "open": open_
    }), 200


@stats_bp.route("/gitlab/merge-ratio", methods=["GET"])
@jwt_required()
def gitlab_merge_ratio():
    user_id = get_jwt_identity()
    project_ids = [p.id for p in GitLabProject.objects()]
    mrs = list(GitLabMergeRequest.objects(project__in=project_ids))

    merged = sum(1 for mr in mrs if getattr(mr, "state", "").lower().strip() == "merged")
    closed = sum(1 for mr in mrs if getattr(mr, "state", "").lower().strip() == "closed")
    conflict = sum(1 for mr in mrs if getattr(mr, "merge_status", "").lower().strip() == "cannot_be_merged")
    open_ = len(mrs) - merged - closed - conflict

    return jsonify({
        "merged": merged,
        "closed": closed,
        "conflict": conflict,
        "open": open_
    }), 200
